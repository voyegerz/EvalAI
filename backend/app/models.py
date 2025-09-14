from datetime import datetime, timezone
from typing import Optional
import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    collections: list["Collection"] = Relationship(back_populates="user", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

class CollectionBase(SQLModel):
    name: str
    branch: str | None = None
    department: str | None = None
    school: str | None = None
    is_evaluated: bool = Field(default=False)
    
class Collection(CollectionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)

    # Relationships to other tables
    user: "User" = Relationship(back_populates="collections")
    ans_pdf_folders: list["AnsPdfFolder"] = Relationship(back_populates="collection", cascade_delete=True)
    qp_pdfs: list["QpPdf"] = Relationship(back_populates="collection", cascade_delete=True)
    evaluation_monitor: "EvaluationMonitor" = Relationship(back_populates="collection")

class AnsPdfFolderBase(SQLModel):
    name: str

class AnsPdfFolder(AnsPdfFolderBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    collection_id: uuid.UUID = Field(foreign_key="collection.id", nullable=False)

    # Relationships
    collection: "Collection" = Relationship(back_populates="ans_pdf_folders")
    ans_pdfs: list["AnsPdf"] = Relationship(back_populates="ans_pdf_folder", cascade_delete=True)
    
class AnsPdfFolderCreate(AnsPdfFolderBase):
    collection_id: uuid.UUID # Required to link to a collection

class AnsPdfFolderPublic(AnsPdfFolderBase):
    id: uuid.UUID
    collection_id: uuid.UUID

class AnsPdfFoldersPublic(SQLModel):
    data: list[AnsPdfFolderPublic]
    count: int

class AnsPdfBase(SQLModel):
    name: str

class AnsPdf(AnsPdfBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ans_pdf_folder_id: uuid.UUID = Field(foreign_key="anspdffolder.id", nullable=False)
    filepath: str
    folder_path: str

    # Relationships
    ans_pdf_folder: "AnsPdfFolder" = Relationship(back_populates="ans_pdfs")
    pages: list["Page"] = Relationship(back_populates="ans_pdf", cascade_delete=True)

class AnsPdfCreate(AnsPdfBase):
    ans_pdf_folder_id: uuid.UUID # Required to link to an AnsPdfFolder
    filepath: str # Path to the saved PDF file
    folder_path: str # Path to the folder containing page images

class AnsPdfPublic(AnsPdfBase):
    id: uuid.UUID
    ans_pdf_folder_id: uuid.UUID
    filepath: str
    folder_path: str

class AnsPdfsPublic(SQLModel):
    data: list[AnsPdfPublic]
    count: int

class QpPdfBase(SQLModel):
    name: str
    filepath: str
    folder_path: str # New field to store the path to the images folder
    json_path: Optional[str] = None

class QpPdf(QpPdfBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    collection_id: uuid.UUID = Field(foreign_key="collection.id", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: "Collection" = Relationship(back_populates="qp_pdfs")

class PageBase(SQLModel):
    page_no: int
    image_path: str
    is_evaluated: bool = Field(default=False)

class Page(PageBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ans_pdf_id: uuid.UUID = Field(foreign_key="anspdf.id", nullable=False)

    # Relationships
    ans_pdf: "AnsPdf" = Relationship(back_populates="pages")
    evaluations: list["Evaluation"] = Relationship(back_populates="page", cascade_delete=True)

class EvaluationBase(SQLModel):
    question_no: str | None = None
    obtained_marks: int
    max_marks: int
    feedback: str
    evaluation_json_path: str | None = None

class Evaluation(EvaluationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    page_id: uuid.UUID = Field(foreign_key="page.id", nullable=False)

    # Relationships
    page: "Page" = Relationship(back_populates="evaluations")

class EvaluationPublic(EvaluationBase):
    id: uuid.UUID
    page_id: uuid.UUID

class EvaluationsPublic(SQLModel):
    data: list[EvaluationPublic]
    count: int

class EvaluationMonitorBase(SQLModel):
    estimated_total: int
    total_pdfs: int
    evaluated_pdfs: int

class EvaluationMonitor(EvaluationMonitorBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    collection_id: uuid.UUID = Field(foreign_key="collection.id", nullable=False, unique=True) # Assumed one-to-one

    # Relationships
    collection: "Collection" = Relationship(back_populates="evaluation_monitor")

class EvaluationMonitorCreate(EvaluationMonitorBase):
    pass

class EvaluationMonitorPublic(EvaluationMonitorBase):
    id: uuid.UUID
    collection_id: uuid.UUID

# You may also want a public list model
class EvaluationMonitorsPublic(SQLModel):
    data: list[EvaluationMonitorPublic]
    count: int

# Properties to receive on collection creation
class CollectionCreate(CollectionBase):
    pass

# Properties to receive on collection update
class CollectionUpdate(SQLModel):
    name: str | None = Field(default=None)
    branch: str | None = Field(default=None)
    department: str | None = Field(default=None)
    school: str | None = Field(default=None)
    is_evaluated: bool | None = Field(default=None)
    
# Properties to return via API, id is always required
class CollectionPublic(CollectionBase):
    id: uuid.UUID
    user_id: uuid.UUID

class CollectionsPublic(SQLModel):
    data: list[CollectionPublic]
    count: int
    
# Properties to receive on QpPdf creation
class QpPdfCreate(QpPdfBase):
    collection_id: uuid.UUID # Required to link to a collection

# Properties to return via API, id is always required
class QpPdfPublic(QpPdfBase):
    id: uuid.UUID
    collection_id: uuid.UUID

class QpPdfsPublic(SQLModel):
    data: list[QpPdfPublic]
    count: int