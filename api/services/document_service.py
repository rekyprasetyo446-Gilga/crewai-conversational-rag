"""
DocumentService: Handles knowledge base file management with traversal protection.
"""

import shutil
import zipfile
from pathlib import Path
from typing import List, BinaryIO
from fastapi import HTTPException

from api.config import settings
from api.schemas.document import DocumentItem, DocumentUploadResponse, DocumentContentResponse, DocumentDeleteResponse


class DocumentService:
    """Manages files in the knowledge directory safely."""

    def __init__(self, knowledge_dir: Path = settings.knowledge_dir):
        self.knowledge_dir = knowledge_dir
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, filename: str) -> Path:
        """Resolves path and guards against directory traversal attacks."""
        safe_name = Path(filename).name
        target_path = (self.knowledge_dir / safe_name).resolve()
        
        # Ensure target is strictly within knowledge directory
        if not str(target_path).startswith(str(self.knowledge_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid file path or directory traversal detected.")
        return target_path

    def list_documents(self) -> List[DocumentItem]:
        """Lists all supported documents in the knowledge directory."""
        if not self.knowledge_dir.exists():
            return []
        
        items = []
        for file_path in self.knowledge_dir.glob("**/*.*"):
            if file_path.suffix.lower() in settings.allowed_extensions and file_path.is_file():
                items.append(DocumentItem(
                    name=file_path.name,
                    size_kb=round(file_path.stat().st_size / 1024, 1),
                    modified=file_path.stat().st_mtime
                ))
        # Sort by recently modified first
        items.sort(key=lambda d: d.modified, reverse=True)
        return items

    def save_document(self, filename: str, file_stream: BinaryIO) -> DocumentUploadResponse:
        """Validates and saves an uploaded file stream into knowledge directory."""
        safe_name = Path(filename).name
        suffix = Path(safe_name).suffix.lower()

        if suffix not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{suffix}'. Allowed: {', '.join(sorted(settings.allowed_extensions))}"
            )

        target_path = self._resolve_safe_path(safe_name)

        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file_stream, buffer)

        # Automatically extract ZIP backups containing PHP/HTML files for RAG
        if suffix == ".zip":
            extract_dir = self.knowledge_dir / target_path.stem
            extract_dir.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(target_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            except Exception:
                pass

        size_kb = round(target_path.stat().st_size / 1024, 1)
        return DocumentUploadResponse(status="success", filename=safe_name, size_kb=size_kb)

    def get_document_content(self, filename: str) -> DocumentContentResponse:
        """Reads textual content of a document in the knowledge base."""
        target_path = self._resolve_safe_path(filename)
        if not target_path.exists() or not target_path.is_file():
            raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")

        try:
            content = target_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not read document '{filename}': {str(e)}")

        size_kb = round(target_path.stat().st_size / 1024, 1)
        return DocumentContentResponse(name=target_path.name, content=content, size_kb=size_kb)

    def delete_document(self, filename: str) -> DocumentDeleteResponse:
        """Deletes a document from the knowledge base."""
        target_path = self._resolve_safe_path(filename)
        if not target_path.exists() or not target_path.is_file():
            raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")

        target_path.unlink()
        return DocumentDeleteResponse(status="deleted", filename=target_path.name)
