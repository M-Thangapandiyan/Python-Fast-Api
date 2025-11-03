"""
Document/Product-related Pydantic schemas.
Note: Currently uses Document naming, but structure matches product pattern.
"""
import uuid
from pydantic import BaseModel, Field
from typing import Optional


class DocumentCreate(BaseModel):
    """
    Schema for creating a new document (without doc_id).
    """
    doc_title: str
    description: Optional[str] = None
    content: Optional[str] = None
    doc_page_count: int 
    is_valid: bool


class Document(DocumentCreate):
    """
    Represents a document with auto-generated UUID.
    Inherits all fields from DocumentCreate and adds doc_id.
    """
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    s3_url: Optional[str] = None

