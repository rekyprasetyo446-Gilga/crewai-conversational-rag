"""
Documents Router: Endpoints for knowledge base file listing, upload, preview, and deletion.
"""

from fastapi import APIRouter, Depends, UploadFile, File, status
from api.dependencies import get_document_service
from api.services.document_service import DocumentService
from api.schemas.document import (
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentContentResponse,
    DocumentDeleteResponse,
)

router = APIRouter(tags=["Knowledge Documents"])


@router.get(
    "/api/documents",
    response_model=DocumentListResponse,
    summary="List all knowledge base documents",
    description="Returns metadata for all indexed documents in the knowledge directory.",
)
async def list_documents_endpoint(
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    docs = doc_service.list_documents()
    return DocumentListResponse(documents=docs)


@router.post(
    "/api/upload",
    response_model=DocumentUploadResponse,
    summary="Upload a new knowledge document",
    description="Validates and persists a file (.md, .txt, .json, .pdf, .csv) into the knowledge base.",
)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    return doc_service.save_document(filename=file.filename, file_stream=file.file)


@router.get(
    "/api/documents/{filename}",
    response_model=DocumentContentResponse,
    summary="View document text content",
    description="Retrieves the textual content and size of a specific knowledge document.",
)
async def get_document_content_endpoint(
    filename: str,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentContentResponse:
    return doc_service.get_document_content(filename)


@router.delete(
    "/api/documents/{filename}",
    response_model=DocumentDeleteResponse,
    summary="Delete a knowledge document",
    description="Removes the specified file from the knowledge base directory.",
)
async def delete_document_endpoint(
    filename: str,
    doc_service: DocumentService = Depends(get_document_service),
) -> DocumentDeleteResponse:
    return doc_service.delete_document(filename)
