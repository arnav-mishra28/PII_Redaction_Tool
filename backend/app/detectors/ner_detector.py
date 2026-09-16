from .regex_detector import Candidate

# Common words / PII field labels that spaCy NER frequently misclassifies as
# PERSON, ORG, or GPE.  Checked case-insensitively so "Email", "EMAIL", and
# "email" are all rejected.
_FALSE_POSITIVE_LABELS: frozenset[str] = frozenset({
    # PII field labels
    "email", "phone", "pan", "aadhaar", "aadhar", "ifsc", "dob",
    "date of birth", "card", "account", "acct", "ip", "address",
    # Common surrounding words spaCy trips on
    "hi", "hello", "dear", "sir", "madam", "mr", "mrs", "ms",
    "contact", "call", "reach", "ship", "send", "support",
    "server", "handle", "number", "no",
})

_MIN_ENTITY_LENGTH = 2  # single-character NER hits are noise


def detect_ner(text: str) -> list[Candidate]:
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            nlp = spacy.blank("en")
        if not nlp.pipe_names or "ner" not in nlp.pipe_names:
            return []
        doc = nlp(text)
        mapping = {
            "PERSON": ("PERSON", 0.82),
            "GPE": ("LOCATION", 0.78),
            "LOC": ("LOCATION", 0.76),
            "ORG": ("ORGANIZATION", 0.76),
        }
        candidates: list[Candidate] = []
        for ent in doc.ents:
            if ent.label_ not in mapping:
                continue
            value = text[ent.start_char:ent.end_char]
            # Skip entities that are too short to be meaningful
            if len(value.strip()) < _MIN_ENTITY_LENGTH:
                continue
            # Skip known false-positive labels / common words
            if value.strip().lower() in _FALSE_POSITIVE_LABELS:
                continue
            entity_type, confidence = mapping[ent.label_]
            candidates.append(
                Candidate(entity_type, ent.start_char, ent.end_char, confidence, "ner")
            )
        return candidates
    except (ImportError, ValueError):
        return []
