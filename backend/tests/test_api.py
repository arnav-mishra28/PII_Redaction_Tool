from fastapi.testclient import TestClient
import fitz

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_text_api_does_not_return_raw_pii():
    response = client.post("/api/v1/redact/text", json={"text": "Email synthetic.user@example.test"})
    assert response.status_code == 200
    body = response.json()
    assert body["redacted_text"] == "Email [REDACTED_EMAIL]"
    assert "synthetic.user@example.test" not in response.text


def test_document_api_returns_extracted_text_for_screen_workflow():
    response = client.post(
        "/api/v1/detect/document",
        files={"file": ("synthetic.txt", b"Email synthetic.user@example.test", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["extracted_text"] == "Email synthetic.user@example.test"


def test_document_file_api_preserves_uploaded_extension_and_redacts_content():
    response = client.post(
        "/api/v1/redact/document/file?masking_mode=typed",
        files={"file": ("ticket.txt", b"Email synthetic.user@example.test", "text/plain")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.headers["content-disposition"] == 'attachment; filename="redacted-ticket.txt"'
    assert b"[REDACTED_EMAIL]" in response.content
    assert b"synthetic.user@example.test" not in response.content


def test_pdf_redaction_removes_entire_formatted_phone():
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Call +91-9640112460 for support")
    response = client.post(
        "/api/v1/redact/document/file?masking_mode=typed",
        files={"file": ("resume.pdf", document.tobytes(), "application/pdf")},
    )
    assert response.status_code == 200
    redacted_text = fitz.open(stream=response.content, filetype="pdf")[0].get_text()
    assert "+91-9640112460" not in redacted_text
    assert "[REDACTED_PHONE]" in redacted_text
