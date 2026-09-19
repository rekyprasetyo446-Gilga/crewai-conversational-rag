"""
Document request and response schemas.
"""

from typing import List
from pydantic import BaseModel, Field


class DocumentItem(BaseModel):
    name: str = Field(..., description="Document file name including extension")
    size_kb: float = Field(..., description="File size in kilobytes")
    modified: float = Field(..., description="Timestamp of last file modification")


class DocumentListResponse(BaseModel):
    documents: List[DocumentItem] = Field(default_factory=list, description="List of knowledge base files")


class DocumentUploadResponse(BaseModel):
    status: str = Field(default="success", description="Upload status")
    filename: str = Field(..., description="Uploaded file name")
    size_kb: float = Field(..., description="Uploaded file size in KB")


class DocumentDeleteResponse(BaseModel):
    status: str = Field(default="deleted", description="Deletion status message")
    filename: str = Field(..., description="Deleted file name")


class DocumentContentResponse(BaseModel):
    name: str = Field(..., description="Document file name")
    content: str = Field(..., description="Textual contents of the document")
    size_kb: float = Field(..., description="File size in KB")
