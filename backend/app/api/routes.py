import json

from fastapi import APIRouter, File, HTTPException, Response, UploadFile

from app.detectors.hybrid import detect_pii
from app.models.schemas import DetectResponse, DocumentResponse, RedactResponse, TextRequest
from app.redaction.service import redact_text
from app.services.document_service import extract_text, redact_document_file

router = APIRouter(prefix="/api/v1")


@router.post("/detect/text", response_model=DetectResponse)
def detect_text(request: TextRequest) -> DetectResponse:
    entities = detect_pii(request.text)
    return DetectResponse(entities=entities, entity_count=len(entities))


@router.post("/redact/text", response_model=RedactResponse)
def redact_text_route(request: TextRequest) -> RedactResponse:
    entities = detect_pii(request.text)
    return RedactResponse(redacted_text=redact_text(request.text, entities, request.masking_mode), entities=entities, entity_count=len(entities))


async def _document(file: UploadFile, redact: bool, masking_mode: str = "typed") -> DocumentResponse:
    try:
        content = await file.read()
        text, media_type = extract_text(file.filename or "upload.txt", content)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=422, detail=f"Could not process document: {error}") from error
    entities = detect_pii(text)
    return DocumentResponse(filename=file.filename or "document", media_type=media_type, extracted_text=text,
                            redacted_text=redact_text(text, entities, masking_mode) if redact else None,
                            entities=entities, entity_count=len(entities), extracted_characters=len(text))


@router.post("/detect/document", response_model=DocumentResponse)
async def detect_document(file: UploadFile = File(...)) -> DocumentResponse:
    return await _document(file, False)


@router.post("/redact/document", response_model=DocumentResponse)
async def redact_document(file: UploadFile = File(...), masking_mode: str = "typed") -> DocumentResponse:
    if masking_mode not in {"typed", "black", "partial"}:
        raise HTTPException(status_code=422, detail="masking_mode must be typed, black, or partial")
    return await _document(file, True, masking_mode)


@router.post("/redact/document/file")
async def redact_document_file_route(file: UploadFile = File(...), masking_mode: str = "typed") -> Response:
    if masking_mode not in {"typed", "black", "partial"}:
        raise HTTPException(status_code=422, detail="masking_mode must be typed, black, or partial")
    filename = file.filename or "document.txt"
    try:
        output, media_type, output_name = redact_document_file(filename, await file.read(), masking_mode)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=422, detail=f"Could not redact document: {error}") from error
    return Response(content=output, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="redacted-{output_name}"'})
