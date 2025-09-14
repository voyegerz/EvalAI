# app/api/routes/download.py

import uuid
from typing import Any
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import select, desc

from app.api.deps import SessionDep, CurrentUser
from app.models import Collection, AnsPdf, AnsPdfFolder, QpPdf

router = APIRouter(prefix="/download", tags=["download"])

# ---------------------------------------------------------
# Endpoint to download a single AnsPdf by its ID
# ---------------------------------------------------------
@router.get("/ans-pdfs/{ans_pdf_id}/", response_class=FileResponse)
def download_ans_pdf(
    session: SessionDep,
    current_user: CurrentUser,
    ans_pdf_id: uuid.UUID,
) -> Any:
    """
    Retrieves and serves the actual PDF file for a given AnsPdf ID.
    """
    ans_pdf = session.get(AnsPdf, ans_pdf_id)
    if not ans_pdf:
        raise HTTPException(status_code=404, detail="Answer PDF not found")

    # Authorization check
    if not current_user.is_superuser:
        ans_pdf_folder = session.get(AnsPdfFolder, ans_pdf.ans_pdf_folder_id)
        if not ans_pdf_folder:
            raise HTTPException(status_code=404, detail="Answer PDF folder not found")
        collection = session.get(Collection, ans_pdf_folder.collection_id)
        if not collection or collection.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions to access this file")

    file_path = Path(ans_pdf.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on server")
    
    return FileResponse(file_path, filename=ans_pdf.name, media_type="application/pdf")


# ---------------------------------------------------------
# Endpoint to download the most recent QpPdf by collection_id
# ---------------------------------------------------------
@router.get("/qppdfs/{collection_id}/", response_class=FileResponse)
def download_qppdf_by_collection(
    session: SessionDep,
    current_user: CurrentUser,
    collection_id: uuid.UUID,
) -> Any:
    """
    Retrieves and serves the most recently uploaded QpPdf for a given collection.
    """
    # Authorization check
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this collection's data")
    
    # Get the most recent QpPdf for this collection
    statement = (
        select(QpPdf)
        .where(QpPdf.collection_id == collection_id)
        .order_by(desc(QpPdf.id)) # Assuming a later ID means a more recent upload
    )
    qppdf = session.exec(statement).first()

    if not qppdf:
        raise HTTPException(status_code=404, detail="Question Paper PDF not found for this collection")

    file_path = Path(qppdf.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on server")

    return FileResponse(file_path, filename=qppdf.name, media_type="application/pdf")