# Veil PII Redaction Tool

Veil is a hybrid NLP system for detecting and redacting personally identifiable information (PII) from raw text and uploaded documents. It is designed for support workflows, internal document handling, and any setting where sensitive information must be protected before text is stored, shared, or reviewed.

The project combines rule-based detection for structured identifiers with named entity recognition for context-sensitive entities such as people, locations, and organizations. The API returns redacted output and entity metadata without exposing matched values inside the response objects.

## Problem Statement

Organizations frequently handle support tickets, forms, reports, and exported records that contain sensitive information such as emails, phone numbers, government identifiers, account numbers, and addresses. Manual redaction is slow, inconsistent, and error-prone. A practical system is needed to automatically identify these entities across both plain text and common document formats, then mask them in a safe and explainable way.

Veil addresses this problem by providing:

- automatic PII detection across text, PDF, DOCX, TXT, JSON, and CSV inputs
- multiple masking strategies for different redaction needs
- metadata-driven outputs using offsets, confidence, risk level, and detection method
- a hybrid pipeline that balances precision for structured PII and flexibility for contextual PII

## Methodology

Veil uses a staged pipeline:

```text
Input -> extraction -> regex detection + NER detection -> candidate merge
      -> confidence and risk tagging -> reverse-order redaction -> protected output
```

### 2.1 Dataset

The repository includes a small synthetic evaluation dataset in `evaluation/dataset.json`. It contains sample texts with labeled spans for categories currently supported by the detector. The dataset is intentionally synthetic so the project can be demonstrated and tested without using real personal information.

Current examples cover:

- `EMAIL`
- `PHONE`
- `PAN`
- `AADHAAR`
- `IFSC`
- `BANK_ACCOUNT`
- `CARD`
- `DATE_OF_BIRTH`
- `IP_ADDRESS`
- `ADDRESS`
- `SOCIAL_HANDLE`

This dataset is used by `evaluation/evaluate.py` to compare expected spans against the entities produced by the hybrid detector.

### 2.2 Preprocessing

Before detection, documents are normalized into text so a single downstream pipeline can process all supported file types.

- TXT, MD, and LOG files are decoded directly as text
- JSON files are parsed and re-serialized into a readable text representation
- CSV files are flattened into newline-separated rows
- PDF files are parsed with PyMuPDF for page-level text extraction
- DOCX files are parsed with `python-docx` to extract paragraph text

After extraction, the detector works only with text spans. This simplifies the pipeline and allows a consistent entity schema across file formats.

### 2.3 Model/Approach

The core approach is hybrid.

Rule-based detection is handled by `backend/app/detectors/regex_detector.py`, which targets structured PII with high precision. The current regex patterns cover identifiers such as email, PAN, Aadhaar-like numbers, IFSC, payment cards, IP addresses, phone numbers, bank account numbers, date of birth formats, social handles, and street-style addresses.

Contextual detection is handled by `backend/app/detectors/ner_detector.py` using spaCy NER when `en_core_web_sm` is available. It maps NER labels into project-level entity types such as `PERSON`, `LOCATION`, and `ORGANIZATION`.

The final detector in `backend/app/detectors/hybrid.py` merges candidates from both sources. When spans overlap, the higher-confidence candidate is kept. Each accepted entity is enriched with:

- `entity_type`
- `start` and `end` offsets
- `confidence`
- `detection_method`
- `risk_level`

Redaction is performed in `backend/app/redaction/service.py`. Spans are replaced from right to left so earlier replacements do not shift later offsets. The tool currently supports three masking modes:

- `typed` -> example: `[REDACTED_EMAIL]`
- `black` -> full block masking
- `partial` -> partial reveal with the remainder masked

### 2.4 Tools and Frameworks

Backend:

- FastAPI
- Pydantic
- spaCy
- PyMuPDF
- python-docx
- pytest

Frontend:

- React
- TypeScript
- Vite
- Tailwind CSS
- `jspdf`
- `docx`

Project structure highlights:

- `backend/app/api/routes.py` exposes detection and redaction endpoints
- `backend/app/services/document_service.py` handles extraction and file redaction
- `backend/app/detectors/` contains regex, NER, and hybrid detection logic
- `evaluation/` contains the synthetic benchmark harness
- `docs/architecture.md` contains the architecture diagram

## Preliminary Results

The current project already demonstrates end-to-end redaction across both text and document workflows.

- structured PII categories are covered by deterministic regex rules
- contextual entity detection is supported through spaCy NER
- API responses avoid returning raw matched values as entity fields
- text redaction, document processing, and PDF phone-number redaction are covered by automated tests in `backend/tests/`
- the repository includes a synthetic benchmark harness for precision, recall, and F1 measurement by category

At this stage, the results should be viewed as a strong functional prototype rather than a final benchmarked system. The synthetic dataset is intentionally small, which is useful for validating detector behavior but not sufficient for claiming production-level accuracy across diverse real-world text.

## Next Steps

- expand the synthetic dataset with more edge cases, noisy formatting, and harder negatives
- fix and harden the evaluation pipeline so category-wise metrics can be reported consistently in every environment
- improve NER coverage for person, location, and organization entities in domain-specific text
- add more context rules to reduce false positives for ambiguous numeric spans
- introduce larger regression test coverage for PDFs, DOCX tables, and mixed-format documents
- add deployment-facing safeguards such as authentication, stricter request limits, and production CORS configuration

## Run Locally

```bash
# backend
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm
PYTHONPATH=backend uvicorn app.main:app --reload

# frontend, in another terminal
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

If the API is not running on port `8000`, set `VITE_API_URL` in `.env`.

## API

- `GET /health`
- `POST /api/v1/detect/text` with `{ "text": "..." }`
- `POST /api/v1/redact/text` with `{ "text": "...", "masking_mode": "typed|black|partial" }`
- `POST /api/v1/detect/document` for PDF, DOCX, TXT, JSON, or CSV uploads
- `POST /api/v1/redact/document` for extracted-text redaction
- `POST /api/v1/redact/document/file` for downloadable redacted files

Entity objects contain `entity_type`, `start`, `end`, `confidence`, `detection_method`, and `risk_level`.

## Evaluation

Run the synthetic evaluation harness with:

```bash
PYTHONPATH=backend python evaluation/evaluate.py
```

The script is intended to print category-wise precision, recall, F1, false positives, and false negatives for the current dataset.

## Security Notes

- uploads are processed in memory and are not persisted by the service
- the API is designed to return entity metadata instead of raw matched values
- production deployment should enforce authentication, TLS, request-size limits, and restricted CORS origins
