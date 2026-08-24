# Veil PII Redaction Tool

Veil is a hybrid NLP service for support tickets and documents. It combines high-precision regex detectors for structured identifiers with spaCy NER for contextual people, places, and organizations. API responses contain offsets and detection metadata only; matched values are never returned as entity fields.

## Run locally

```bash
# backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm
PYTHONPATH=backend uvicorn app.main:app --reload

# frontend, in another terminal
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. Set `VITE_API_URL` in `.env` when the API is not on port 8000.

## Docker

```bash
docker compose up --build
```

The UI is at `http://localhost:5173` and the API at `http://localhost:8000`.

## API

- `GET /health`
- `POST /api/v1/detect/text` with `{ "text": "..." }`
- `POST /api/v1/redact/text` with `{ "text": "...", "masking_mode": "typed|black|partial" }`
- `POST /api/v1/detect/document` multipart upload for PDF, DOCX, TXT, JSON, or CSV
- `POST /api/v1/redact/document` multipart upload with optional `masking_mode`

Entity objects have `entity_type`, `start`, `end`, `confidence`, `detection_method`, and `risk_level`. Offsets are Python string offsets into the extracted text.

## Architecture

```text
Input -> extraction -> regex + spaCy NER -> context-aware candidates
      -> overlap arbitration -> confidence/risk metadata -> reverse-span redaction -> output
```

`backend/app/detectors/regex_detector.py` owns structured patterns. `ner_detector.py` loads `en_core_web_sm` when available and safely returns no NER candidates when the model is unavailable. `hybrid.py` merges overlapping detections, favoring the highest-confidence candidate. `redaction/service.py` replaces spans from right to left so offsets stay valid.

Structured categories include email, phone, PAN, Aadhaar-like numbers, bank account numbers, IFSC, payment cards, IP addresses, DOB, addresses, and social handles. NER categories include person, location, and organization.

## Evaluation

The included dataset is synthetic and contains no real personal information. Run:

```bash
PYTHONPATH=backend python evaluation/evaluate.py
```

This prints precision, recall, F1, false positives, and false negatives for every category. Add synthetic examples to `evaluation/dataset.json` as the detector evolves.

## Security notes

Uploads are processed in memory and are not persisted. The API does not log request bodies or matched values. For production, put the service behind authentication, enforce request size limits at the proxy, use TLS, and configure a restricted CORS origin.
