# app/api/routes/upload.py

import shutil
from pathlib import Path
import uuid
from typing import Any
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException, Form
import fitz
from sqlmodel import select, func, join

from app.api.deps import SessionDep, CurrentUser, get_session
from app.models import (
    Collection,
    AnsPdfFolder,
    AnsPdfFolderCreate,
    AnsPdfFolderPublic,
    AnsPdfFoldersPublic,
    AnsPdf,
    AnsPdfCreate,
    AnsPdfPublic,
    AnsPdfsPublic,
    Page,
    QpPdf,
    QpPdfCreate,
    QpPdfPublic,
    QpPdfsPublic
)

import asyncio
import json
import logging
from app.services.llm_service import LLMService
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize LLM service
llm_service = LLMService(api_key=settings.GEMINI_API_KEY)

router = APIRouter(prefix="/upload", tags=["upload"])

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def process_qp_images(
    qp_pdf_folder: Path, qp_pdf_id: uuid.UUID
):
    """
    Background task to handle image processing and LLM interaction.
    """
    with get_session() as session:
        try:
            image_files = sorted(qp_pdf_folder.glob("*.png"))
            
            image_paths = [str(p) for p in image_files]
            
            prompt = """
    You are an intelligent exam paper parser.
    Your task is to analyze the content of the provided question paper images and extract all questions with their metadata.

    Rules:

    Output must be a single valid JSON object only (no extra text).

    Follow the schema strictly.

    Max Marks Rules:

    If a section says “Answer any TWO out of four (10 marks)”, then each sub-question is worth total_marks / required_questions → here 10/2 = 5 marks each.

    If more sub-questions are attempted than required, only the highest-scoring ones should be counted (this logic should be reflected in the max_marks of each sub-question).

    For MCQs, each question carries equal marks as mentioned (or assume 1 mark if not specified, also for mcqs parse the options with their numbering like 
    a. option 1
    b. option 2
    c. option 3
    d. option 4
    or 
    1. option 1
    2. option 2
    3. option 3
    4. option 4
    and in the correct_answer:"string" store the evaluated correct option for that mcq).

    If a question or option cannot be parsed, omit it.
    JSON Schema to follow:
    {
    "exam_details": {
        "name": "string",
        "course_code": "string",
        "marks": "number",
        "date": "string",
        "time": "string"
    },
    "sections": [
        {
        "section_name": "string",
        "instructions": "string",
        "questions": [
            {
            "question_number": "number",
            "question_text": "string",
            "question_type": "string", 
            "options": ["array of strings"], 
            "correct_answer": "string", 
            "max_marks": "number"
            }
        ]
        }
    ]
    }

    Return only a valid JSON object.
    Do not include markdown, code fences, or extra text.
            """
            
            llm_response_str = await llm_service.process_images(
                image_paths=image_paths,
                prompt=prompt
            )

            # Handle potential non-JSON responses from the LLM
            try:
                # Strip markdown code fences if present
                cleaned_response = llm_response_str.strip()
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response.strip("`")
                    # remove the first line (```json or ```)
                    cleaned_response = "\n".join(cleaned_response.split("\n")[1:])
                    # remove the last line (closing ```)
                    if cleaned_response.strip().endswith("```"):
                        cleaned_response = "\n".join(cleaned_response.split("\n")[:-1])
                        
                qp_data = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"LLM response was not valid JSON: {e}")
                logger.error(f"LLM response was: {llm_response_str}")
                # You might want to update the DB with an error status here
                return

            # Save the JSON data to a file
            json_file_path = qp_pdf_folder / "qp_data.json"
            with open(json_file_path, "w") as f:
                json.dump(qp_data, f, indent=4)
            
            # Update the QpPdf record with the JSON file path
            qp_pdf = session.get(QpPdf, qp_pdf_id)
            if qp_pdf:
                qp_pdf.json_path = str(json_file_path)
                session.add(qp_pdf)
                session.commit()
                session.refresh(qp_pdf)
                logger.info(f"Question paper data saved to {json_file_path} and DB updated.")
        
        except Exception as e:
            logger.error(f"Background task for QpPdf processing failed: {e}")


# ---------------------------------------------------------
# New endpoint for creating an AnsPdfFolder
# ---------------------------------------------------------
@router.post(
    "/ans-pdf-folders/",
    response_model=AnsPdfFolderPublic,
    status_code=201,
)
async def create_ans_pdf_folder(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    collection_id: uuid.UUID = Form(...),
) -> Any:
    """
    Create a new folder for answer sheets and link it to a collection.
    The folder name will be automatically generated using a UUID.
    """
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found.")

    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to add a folder to this collection.")

    try:
        # Generate a UUID-based name for the AnsPdfFolder
        generated_name = f"ans_pdf_folder_{uuid.uuid4().hex}"
        
        # Create the physical directory on the server
        folder_path = UPLOAD_DIR / generated_name
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Create a database record for the folder
        ans_pdf_folder_in = AnsPdfFolderCreate(name=generated_name, collection_id=collection_id)
        ans_pdf_folder = AnsPdfFolder.model_validate(ans_pdf_folder_in)
        session.add(ans_pdf_folder)
        session.commit()
        session.refresh(ans_pdf_folder)

        return ans_pdf_folder
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create answer PDF folder: {str(e)}")

# ---------------------------------------------------------
# New endpoint for uploading an AnsPdf (actual PDF and images)
# ---------------------------------------------------------
@router.post(
    "/ans-pdfs/",
    response_model=AnsPdfPublic,
    status_code=201,
)
async def upload_ans_pdf(
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    ans_pdf_folder_id: uuid.UUID = Form(...),
) -> Any:
    """
    Upload an answer sheet PDF, convert it to images, and link to an existing AnsPdfFolder.
    """
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # Validate AnsPdfFolder existence and ownership
    ans_pdf_folder = session.get(AnsPdfFolder, ans_pdf_folder_id)
    if not ans_pdf_folder:
        raise HTTPException(status_code=404, detail=f"Answer PDF folder with ID {ans_pdf_folder_id} not found.")

    # Check if the user owns the collection that the ans_pdf_folder belongs to
    collection = session.get(Collection, ans_pdf_folder.collection_id)
    if not collection: # Should not happen if data integrity is maintained
         raise HTTPException(status_code=500, detail="Associated collection not found for the answer PDF folder.")
    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to add PDF to this folder.")

    try:
        # Create a unique folder for this specific PDF's images
        pdf_name_stem = Path(file.filename).stem
        unique_id = uuid.uuid4().hex[:8]
        # Images will be stored in a subfolder named after the PDF name + unique ID
        ans_pdf_images_folder = UPLOAD_DIR / ans_pdf_folder.name / f"{pdf_name_stem}_{unique_id}"
        ans_pdf_images_folder.mkdir(parents=True, exist_ok=True)
        
        # Define the full path for the PDF file (saved inside the images folder)
        pdf_path = ans_pdf_images_folder / Path(file.filename).name

        # Save the uploaded PDF file
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convert each page of the PDF into a PNG image
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):  # type: ignore
            pix = page.get_pixmap()
            image_path = ans_pdf_images_folder / f"page{i + 1}.png"
            pix.save(image_path)
        doc.close()
        
        # Create an AnsPdf record in the database
        ans_pdf_in = AnsPdfCreate(
            name=file.filename,
            filepath=str(pdf_path),
            folder_path=str(ans_pdf_images_folder),
            ans_pdf_folder_id=ans_pdf_folder_id,
        )
        ans_pdf = AnsPdf.model_validate(ans_pdf_in)
        session.add(ans_pdf)
        session.commit()
        session.refresh(ans_pdf)

        return ans_pdf

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer PDF upload and conversion failed: {str(e)}")


# ---------------------------------------------------------
# New endpoint for uploading AnsPdf directly with collection_id
# ---------------------------------------------------------
@router.post(
    "/ans-pdfs/by-collection/",
    response_model=AnsPdfPublic,
    status_code=201,
)
async def upload_ans_pdf_to_collection(
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    collection_id: uuid.UUID = Form(...),
) -> Any:
    """
    Upload an answer sheet PDF, convert it to images, link to a new AnsPdfFolder,
    and create a database record for each page.
    """
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found.")
    
    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to add PDF to this collection.")

    try:
        # Create a new AnsPdfFolder
        generated_folder_name = f"ans_pdf_folder_{uuid.uuid4().hex}"
        ans_pdf_root_folder_path = UPLOAD_DIR / generated_folder_name
        ans_pdf_root_folder_path.mkdir(parents=True, exist_ok=True)
        ans_pdf_folder_in = AnsPdfFolderCreate(name=generated_folder_name, collection_id=collection_id)
        ans_pdf_folder = AnsPdfFolder.model_validate(ans_pdf_folder_in)
        session.add(ans_pdf_folder)
        session.commit()
        session.refresh(ans_pdf_folder)
        
        # Save file and convert to images
        pdf_name_stem = Path(file.filename).stem
        unique_id = uuid.uuid4().hex[:8]
        ans_pdf_images_folder = ans_pdf_root_folder_path / f"{pdf_name_stem}_{unique_id}"
        ans_pdf_images_folder.mkdir(parents=True, exist_ok=True)
        pdf_path = ans_pdf_images_folder / Path(file.filename).name
        
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        doc = fitz.open(pdf_path)
        page_image_paths = []
        for i, page in enumerate(doc):  # type: ignore
            image_path = ans_pdf_images_folder / f"page{i + 1}.png"
            pix = page.get_pixmap()
            pix.save(image_path)
            page_image_paths.append(str(image_path))
        doc.close()
        
        # Create an AnsPdf record
        ans_pdf_in = AnsPdfCreate(
            name=file.filename,
            filepath=str(pdf_path),
            folder_path=str(ans_pdf_images_folder),
            ans_pdf_folder_id=ans_pdf_folder.id,
        )
        ans_pdf = AnsPdf.model_validate(ans_pdf_in)
        session.add(ans_pdf)
        session.commit()
        session.refresh(ans_pdf)

        # ⭐ New Logic: Create a Page record for each image
        for i, image_path in enumerate(page_image_paths):
            page_in = Page(
                page_no=i + 1,
                image_path=image_path,
                ans_pdf_id=ans_pdf.id
            )
            session.add(page_in)
        
        session.commit()
        session.refresh(ans_pdf)

        return ans_pdf

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer PDF upload and conversion failed: {str(e)}")

# ---------------------------------------------------------
# New endpoint for Question Paper PDF upload
# ---------------------------------------------------------

@router.post(
    "/qppdf/",
    response_model=QpPdfPublic,
    status_code=201,
)
async def upload_qppdf(
    session: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_id: uuid.UUID = Form(...),
) -> Any:
    """
    Upload a Question Paper (PDF), convert it to images, and link to a collection.
    """
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection with ID {collection_id} not found.")
    
    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to add a question paper to this collection.")

    try:
        qp_pdf_name = Path(file.filename).stem
        unique_id = uuid.uuid4().hex[:8]
        qp_pdf_folder = UPLOAD_DIR / f"{qp_pdf_name}_qp_{unique_id}"
        qp_pdf_folder.mkdir(exist_ok=True)

        file_location = qp_pdf_folder / Path(file.filename).name

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc = fitz.open(file_location)
        for i, page in enumerate(doc):  # type: ignore
            pix = page.get_pixmap()
            image_path = qp_pdf_folder / f"page{i + 1}.png"
            pix.save(image_path)
        doc.close()

        qp_pdf_in = QpPdfCreate(
            name=file.filename,
            filepath=str(file_location),
            folder_path=str(qp_pdf_folder),
            collection_id=collection_id,
        )
        qp_pdf = QpPdf.model_validate(qp_pdf_in)
        session.add(qp_pdf)
        session.commit()
        session.refresh(qp_pdf)
        
        # Add the new background task to process the images with the LLM
        background_tasks.add_task(process_qp_images, qp_pdf_folder, qp_pdf.id)

        return qp_pdf

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question paper upload and conversion failed: {str(e)}")


# ---------------------------------------------------------
# New GET endpoints for AnsPdfFolder
# ---------------------------------------------------------
@router.get("/ans-pdf-folders/", response_model=AnsPdfFoldersPublic)
def read_ans_pdf_folders(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve a list of answer sheet folders.
    Superusers get all folders, regular users get folders from their own collections.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(AnsPdfFolder)
        count = session.exec(count_statement).one()
        statement = select(AnsPdfFolder).offset(skip).limit(limit)
        ans_pdf_folders = session.exec(statement).all()
    else:
        statement = (
            select(AnsPdfFolder)
            .join(Collection)
            .where(Collection.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        ans_pdf_folders = session.exec(statement).all()

        count_statement = (
            select(func.count())
            .select_from(AnsPdfFolder)
            .join(Collection)
            .where(Collection.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()

    return AnsPdfFoldersPublic(data=ans_pdf_folders, count=count) # type: ignore


@router.get("/ans-pdf-folders/{id}", response_model=AnsPdfFolderPublic)
def read_ans_pdf_folder(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get a single answer sheet folder by ID.
    """
    ans_pdf_folder = session.get(AnsPdfFolder, id)
    if not ans_pdf_folder:
        raise HTTPException(status_code=404, detail="Answer PDF folder not found")

    if not current_user.is_superuser:
        collection = session.get(Collection, ans_pdf_folder.collection_id)
        if not collection or collection.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return ans_pdf_folder


# ---------------------------------------------------------
# New GET endpoints for AnsPdf
# ---------------------------------------------------------
@router.get("/ans-pdfs/", response_model=AnsPdfsPublic)
def read_ans_pdfs(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve a list of uploaded answer sheet PDFs.
    Superusers get all PDFs, regular users get PDFs from their own collections.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(AnsPdf)
        count = session.exec(count_statement).one()
        statement = select(AnsPdf).offset(skip).limit(limit)
        ans_pdfs = session.exec(statement).all()
    else:
        statement = (
            select(AnsPdf)
            .join(AnsPdfFolder)
            .join(Collection)
            .where(Collection.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        ans_pdfs = session.exec(statement).all()

        count_statement = (
            select(func.count())
            .select_from(AnsPdf)
            .join(AnsPdfFolder)
            .join(Collection)
            .where(Collection.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()

    return AnsPdfsPublic(data=ans_pdfs, count=count) # type: ignore


@router.get("/ans-pdfs/{id}", response_model=AnsPdfPublic)
def read_ans_pdf(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get a single uploaded answer sheet PDF by ID.
    """
    ans_pdf = session.get(AnsPdf, id)
    if not ans_pdf:
        raise HTTPException(status_code=404, detail="Answer PDF not found")

    if not current_user.is_superuser:
        ans_pdf_folder = session.get(AnsPdfFolder, ans_pdf.ans_pdf_folder_id)
        if not ans_pdf_folder:
            raise HTTPException(status_code=404, detail="Answer PDF folder not found")
        collection = session.get(Collection, ans_pdf_folder.collection_id)
        if not collection or collection.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return ans_pdf

# ---------------------------------------------------------
# New GET endpoint to get AnsPdfs by collection ID
# ---------------------------------------------------------
@router.get("/ans-pdfs/by-collection/{collection_id}", response_model=AnsPdfsPublic)
def get_ans_pdfs_by_collection(
    session: SessionDep,
    current_user: CurrentUser,
    collection_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all answer sheet PDFs for a specific collection.
    """
    # Authorization check: Ensure the user has permission to access this collection
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this collection's data")

    # Select all AnsPdf records that belong to this collection
    # The where clause compares the column (AnsPdfFolder.collection_id)
    # to the provided UUID variable (collection_id)
    statement = (
        select(AnsPdf)
        .join(AnsPdfFolder)
        .where(AnsPdfFolder.collection_id == collection_id)
        .offset(skip)
        .limit(limit)
    )
    ans_pdfs = session.exec(statement).all()

    # Get the total count
    count_statement = (
        select(func.count())
        .select_from(AnsPdf)
        .join(AnsPdfFolder)
        .where(AnsPdfFolder.collection_id == collection_id)
    )
    count = session.exec(count_statement).one()

    return AnsPdfsPublic(data=ans_pdfs, count=count) # type: ignore

# ---------------------------------------------------------
# New GET endpoints for QpPdf
# ---------------------------------------------------------
@router.get("/qppdfs/", response_model=QpPdfsPublic)
def read_qppdfs(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve a list of uploaded Question Paper PDFs.
    Superusers get all QpPdfs, regular users get QpPdfs from their own collections.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(QpPdf)
        count = session.exec(count_statement).one()
        statement = select(QpPdf).offset(skip).limit(limit)
        qppdfs = session.exec(statement).all()
    else:
        statement = (
            select(QpPdf)
            .join(Collection)
            .where(Collection.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        qppdfs = session.exec(statement).all()

        count_statement = (
            select(func.count())
            .select_from(QpPdf)
            .join(Collection)
            .where(Collection.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()

    return QpPdfsPublic(data=qppdfs, count=count) # type: ignore


@router.get("/qppdfs/{id}", response_model=QpPdfPublic)
def read_qppdf(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get a single uploaded Question Paper PDF by ID.
    """
    qppdf = session.get(QpPdf, id)
    if not qppdf:
        raise HTTPException(status_code=404, detail="Question Paper PDF not found")

    if not current_user.is_superuser:
        collection = session.get(Collection, qppdf.collection_id)
        if not collection or collection.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return qppdf

# ---------------------------------------------------------
# New GET endpoint to get QpPdfs by collection ID
# ---------------------------------------------------------
@router.get("/qppdfs/by-collection/{collection_id}", response_model=QpPdfsPublic)
def get_qppdfs_by_collection(
    session: SessionDep,
    current_user: CurrentUser,
    collection_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all question paper PDFs for a specific collection.
    """
    # Authorization check: Ensure the user has permission to access this collection
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this collection's data")

    # Select all QpPdf records that belong to this collection
    statement = (
        select(QpPdf)
        .where(QpPdf.collection_id == collection_id)
        .offset(skip)
        .limit(limit)
    )
    qppdfs = session.exec(statement).all()

    # Get the total count
    count_statement = (
        select(func.count())
        .select_from(QpPdf)
        .where(QpPdf.collection_id == collection_id)
    )
    count = session.exec(count_statement).one()

    return QpPdfsPublic(data=qppdfs, count=count) # type: ignore