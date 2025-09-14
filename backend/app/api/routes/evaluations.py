# app/api/routes/evaluations.py

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, join

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    AnsPdf,
    AnsPdfFolder,
    Collection,
    Evaluation,
    EvaluationPublic,
    EvaluationsPublic,
    Page,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/by-collection/{collection_id}", response_model=EvaluationsPublic)
def read_evaluations_by_collection(
    session: SessionDep,
    current_user: CurrentUser,
    collection_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all evaluations for a specific collection.
    """
    # Authorization check: Ensure the user has permission to access this collection
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not current_user.is_superuser and collection.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not enough permissions to access this collection's data"
        )

    # Select evaluations by joining through the entire hierarchy
    statement = (
        select(Evaluation)
        .join(Page)
        .join(AnsPdf)
        .join(AnsPdfFolder)
        .join(Collection)
        .where(Collection.id == collection_id)
        .offset(skip)
        .limit(limit)
    )
    evaluations = session.exec(statement).all()

    # Get the total count
    count_statement = (
        select(func.count(Evaluation.id)) # type: ignore
        .join(Page)
        .join(AnsPdf)
        .join(AnsPdfFolder)
        .join(Collection)
        .where(Collection.id == collection_id)
    )
    count = session.exec(count_statement).one()

    return EvaluationsPublic(data=evaluations, count=count) # type: ignore