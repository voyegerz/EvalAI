# app/api/routes/evaluate.py


from typing import Dict, Any, List
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlmodel import select, func, join, desc
import json
import logging
import asyncio
import uuid

from app.services.llm_service import LLMService
from app.core.config import settings
from app.api.deps import SessionDep, CurrentUser, get_session
from app.models import (
    AnsPdf,
    AnsPdfFolder,
    Collection,
    Evaluation,
    Page,
    QpPdf,
    EvaluationMonitor,
    EvaluationMonitorCreate,
    EvaluationMonitorPublic,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluate", tags=["evaluate"])

# Initialize LLM service
llm_service = LLMService(api_key=settings.GEMINI_API_KEY)

# Define the root directory for uploads and evaluations
UPLOAD_DIR = Path("uploads")


@router.post("/{collection_id}/", status_code=200)
async def evaluate_answersheet(
    session: SessionDep,
    current_user: CurrentUser,
    collection_id: uuid.UUID,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Initiate the evaluation for all answer sheets in a collection.
    """
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found.")

    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this collection.")

    # Find the most recently uploaded QpPdf for this collection
    qp_pdf = session.exec(
        select(QpPdf)
        .where(QpPdf.collection_id == collection_id)
        .order_by(desc(QpPdf.created_at))
    ).first()

    if not qp_pdf or not qp_pdf.json_path:
        raise HTTPException(
            status_code=404,
            detail="No valid question paper found for this collection. Please upload and process one first."
        )

    # Count total AnsPdfs to initialize the monitor
    total_pdfs_statement = (
        select(func.count(AnsPdf.id)) # type: ignore
        .join(AnsPdfFolder)
        .where(AnsPdfFolder.collection_id == collection_id)
    )
    total_pdfs = session.exec(total_pdfs_statement).one()

    # Create or update the EvaluationMonitor record
    monitor_record = session.exec(
        select(EvaluationMonitor)
        .where(EvaluationMonitor.collection_id == collection_id)
    ).first()
    
    if monitor_record:
        monitor_record.total_pdfs = total_pdfs
        monitor_record.evaluated_pdfs = 0
    else:
        monitor_record = EvaluationMonitor(
            collection_id=collection_id,
            estimated_total=0, # This can be updated in the background task
            total_pdfs=total_pdfs,
            evaluated_pdfs=0,
        )
    session.add(monitor_record)
    session.commit()
    session.refresh(monitor_record)
    
    background_tasks.add_task(
        process_evaluation_for_collection, collection_id, qp_pdf.id
    )

    return {"message": "Evaluation process for the collection started in the background."}


async def process_evaluation_for_collection(collection_id: uuid.UUID, qp_pdf_id: uuid.UUID):
    """
    Background task to handle image processing and evaluation.
    This task creates its own database session.
    """
    await asyncio.sleep(1)
    try:
        with get_session() as session:
            monitor_record = session.exec(
                            select(EvaluationMonitor)
                            .where(EvaluationMonitor.collection_id == collection_id)
                            ).first()
            qp_pdf = session.get(QpPdf, qp_pdf_id)

            if not qp_pdf or not qp_pdf.json_path or not monitor_record:
                logger.error("Background task failed: QpPdf, monitor record, or its JSON data not found.")
                return

            if not qp_pdf.json_path:
                logger.error("QpPdf json_path is None.")
                return
            qp_data_path = Path(qp_pdf.json_path)
            if not qp_data_path or not qp_data_path.exists():
                logger.error(f"QpData JSON file not found at: {qp_data_path}")
                return
            
            with open(qp_data_path, "r") as f:
                qp_data = json.load(f)
            

            all_ans_pdfs = session.exec(
                select(AnsPdf)
                .join(AnsPdfFolder)
                .where(AnsPdfFolder.collection_id == collection_id)
            ).all()

            for ans_pdf in all_ans_pdfs:
                pages = session.exec(
                    select(Page).where(Page.ans_pdf_id == ans_pdf.id)
                ).all()

                
                for page in pages:
                    try:
                        
                        # New prompt for per-page evaluation
                        page_evaluation_prompt = (
                            "You are an intelligent exam evaluator. You will be provided with a student's answer sheet page and the structured question data from the question paper. "
                            "Your task is to: "
                            "1. Identify the main section number (e.g., Q1, Q2) from the page. "
                            "2. Identify each sub-question number (e.g., 1, 2, 3) within that section. "
                            "3. Combine them to form a complete question number in the format 'section.sub_question' (e.g., '1.1', '2.3'). "
                            "4. Evaluate the student's handwritten answer for each question found on the page. "
                            "5. Return a JSON object with a list of evaluation results, one for each question found."
                            "\n\nJSON Schema:\n["
                            "  {"
                            "    \"question_no\": \"string\" (e.g., '1.1', '2.3'),"
                            "    \"obtained_marks\": \"number\","
                            "    \"max_marks\": \"number\","
                            "    \"feedback\": \"string\""
                            "  }"
                            "]"
                            "Do not include any extra text."
                            f"\n\nQuestion Paper Data: {json.dumps(qp_data, indent=4)}"
                            "\n\nStudent Answer Sheet Page Image:"
                        )
                        
                        image_path = Path(page.image_path)
                        eval_result_str = await llm_service.process_images(
                            image_paths=[str(image_path)], prompt=page_evaluation_prompt
                        )
                        
                        cleaned_response = eval_result_str.strip()
                        if cleaned_response.startswith("```"):
                            cleaned_response = cleaned_response.strip("`")
                            cleaned_response = "\n".join(cleaned_response.split("\n")[1:])
                            if cleaned_response.strip().endswith("```"):
                                cleaned_response = "\n".join(cleaned_response.split("\n")[:-1])
                                
                        safe_response = cleaned_response.replace("\\", "\\\\")

                        # Try to parse the LLM's response
                        eval_data = json.loads(safe_response)
                        
                        # Save the raw JSON response to a file
                        eval_folder = Path(page.image_path).parent / "evaluation"
                        eval_folder.mkdir(exist_ok=True)
                        eval_file_path = eval_folder / f"{page.id}_result.json"
                        
                        with open(eval_file_path, "w") as f:
                            json.dump(eval_data, f, indent=4)

                        # Loop through the parsed data and create a new Evaluation record for each result
                        for evaluation_item in eval_data:
                            evaluation_record = Evaluation(
                                question_no=evaluation_item.get("question_no"),
                                obtained_marks=evaluation_item.get("obtained_marks"),
                                max_marks=evaluation_item.get("max_marks"),
                                feedback=evaluation_item.get("feedback"),
                                evaluation_json_path=str(eval_file_path), # Store the path to the raw JSON
                                page_id=page.id,
                            )
                            session.add(evaluation_record)
                        
                        # Mark the page as evaluated and commit all changes
                        page.is_evaluated = True
                        session.add(page)
                        
                        logger.info(f"Evaluation for Page {page.id} completed and records saved.")
                
                    except json.JSONDecodeError as e:
                        logger.error(f"LLM response was not valid JSON for page {page.id}: {e}")
                    except Exception as e:
                        logger.error(f"Evaluation failed for page {page.id}: {e}")
                        
                monitor_record.evaluated_pdfs += 1
                session.add(monitor_record)
                session.commit()
            
            # Finally, mark the collection as evaluated if all PDFs are done
            if monitor_record.evaluated_pdfs >= monitor_record.total_pdfs:
                collection = session.get(Collection, collection_id)
                if collection:
                    collection.is_evaluated = True
                    session.add(collection)
                    session.commit()
                
    except Exception as e:
        logger.error(f"Background evaluation task failed: {e}")