"""
Automated unit and integration tests for the modular FastAPI application.
"""

import io
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_ui_index():
    """Verify that GET / returns 200 OK and serves HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in response.text


def test_health_check():
    """Verify GET /api/health returns healthy status and metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "model_configured" in data
    assert "active_sessions" in data
    assert "total_documents" in data


def test_status_endpoint():
    """Verify GET /api/status returns active model and settings."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "model" in data
    assert "knowledge_dir" in data


def test_chat_validation():
    """Verify POST /api/chat returns 400 when message is empty."""
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
    assert "Message cannot be empty" in response.json()["detail"]


def test_memory_clear_and_history():
    """Verify POST /api/clear and GET /api/chat/history."""
    # Test clear
    clear_resp = client.post("/api/clear?session_id=test_session")
    assert clear_resp.status_code == 200
    clear_data = clear_resp.json()
    assert clear_data["status"] == "Memory cleared"
    assert clear_data["turns"] == 0
    assert clear_data["session_id"] == "test_session"

    # Test history retrieval
    hist_resp = client.get("/api/chat/history?session_id=test_session")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["session_id"] == "test_session"
    assert hist_data["turns"] == 0
    assert isinstance(hist_data["history"], list)


def test_document_lifecycle():
    """Test full document workflow: upload, list, preview content, and delete."""
    test_filename = "test_fastapi_doc.md"
    test_content = "# FastAPI Modular Architecture\nTested successfully."

    # 1. Upload
    file_bytes = io.BytesIO(test_content.encode("utf-8"))
    upload_resp = client.post(
        "/api/upload",
        files={"file": (test_filename, file_bytes, "text/markdown")}
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["status"] == "success"
    assert upload_data["filename"] == test_filename

    # 2. List documents
    list_resp = client.get("/api/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json().get("documents", [])
    doc_names = [d["name"] for d in docs]
    assert test_filename in doc_names

    # 3. Read content
    content_resp = client.get(f"/api/documents/{test_filename}")
    assert content_resp.status_code == 200
    content_data = content_resp.json()
    assert content_data["name"] == test_filename
    assert "FastAPI Modular Architecture" in content_data["content"]

    # 4. Delete document
    del_resp = client.delete(f"/api/documents/{test_filename}")
    assert del_resp.status_code == 200
    del_data = del_resp.json()
    assert del_data["status"] == "deleted"

    # 5. Verify deleted
    verify_resp = client.get(f"/api/documents/{test_filename}")
    assert verify_resp.status_code == 404


if __name__ == "__main__":
    print("Running automated FastAPI tests...")
    test_ui_index()
    print("✓ test_ui_index passed")
    test_health_check()
    print("✓ test_health_check passed")
    test_status_endpoint()
    print("✓ test_status_endpoint passed")
    test_chat_validation()
    print("✓ test_chat_validation passed")
    test_memory_clear_and_history()
    print("✓ test_memory_clear_and_history passed")
    test_document_lifecycle()
    print("✓ test_document_lifecycle passed")
    print("\nALL FASTAPI TESTS PASSED SUCCESSFULLY! 🎉")

