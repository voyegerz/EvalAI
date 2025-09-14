# app/api/routes/collections.py

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Collection,
    CollectionCreate,
    CollectionPublic,
    CollectionsPublic,
    CollectionUpdate,
    Message,
)

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/", response_model=CollectionsPublic)
def read_collections(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve collections.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Collection)
        count = session.exec(count_statement).one()
        statement = select(Collection).offset(skip).limit(limit)
        collections = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Collection)
            .where(Collection.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Collection)
            .where(Collection.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        collections = session.exec(statement).all()

    return CollectionsPublic(data=collections, count=count) # type: ignore


@router.get("/{id}", response_model=CollectionPublic)
def read_collection(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get collection by ID.
    """
    collection = session.get(Collection, id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not current_user.is_superuser and (collection.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return collection


@router.post("/", response_model=CollectionPublic, status_code=201)
def create_collection(
    *, session: SessionDep, current_user: CurrentUser, collection_in: CollectionCreate
) -> Any:
    """
    Create a new collection.
    """
    collection = Collection.model_validate(collection_in, update={"user_id": current_user.id})
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


@router.put("/{id}", response_model=CollectionPublic)
def update_collection(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    collection_in: CollectionUpdate,
) -> Any:
    """
    Update a collection.
    """
    collection = session.get(Collection, id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not current_user.is_superuser and (collection.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = collection_in.model_dump(exclude_unset=True)
    collection.sqlmodel_update(update_dict)
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


@router.delete("/{id}")
def delete_collection(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a collection.
    """
    collection = session.get(Collection, id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not current_user.is_superuser and (collection.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(collection)
    session.commit()
    return Message(message="Collection deleted successfully")