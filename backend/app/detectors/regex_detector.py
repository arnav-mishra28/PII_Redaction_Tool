import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    entity_type: str
    start: int
    end: int
    confidence: float
    method: str = "regex"


PATTERNS: tuple[tuple[str, str, float], ...] = (
    ("EMAIL", r"(?i)(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w-])", 0.99),
    ("PAN", r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", 0.99),
    ("IFSC", r"\b[A-Z]{4}0[A-Z0-9]{6}\b", 0.98),
    ("AADHAAR", r"(?<!\d)(?:\d{4}[ -]){2}\d{4}(?!\d)", 0.97),
    ("CARD", r"(?<!\d)(?:(?:\d{4}[ -]){3}\d{4}|\d{13,19})(?!\d)", 0.99),
    ("IP_ADDRESS", r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b", 0.98),
    ("PHONE", r"(?<!\w)(?:\+?\d{1,3}[ .-]?)?(?:\(?\d{2,4}\)?[ .-]?)?(?:\d{5}[ .-]?\d{5}|\d{3,4}[ .-]?\d{4})(?!\w)", 0.94),
    ("BANK_ACCOUNT", r"(?i)\b(?:account|a/c|acct)\s*(?:number|no|#)?\s*[:=-]?\s*(\d{9,18})\b", 0.99),
    ("DATE_OF_BIRTH", r"(?i)\b(?:dob|date of birth|birth date)\s*[:=-]?\s*((?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}))", 0.96),
    ("SOCIAL_HANDLE", r"(?<!\w)@[A-Za-z][A-Za-z0-9_.-]{2,30}\b", 0.88),
    ("ADDRESS", r"(?i)\b\d{1,5}\s+[A-Za-z0-9][A-Za-z0-9 .,'-]{2,50}\s+(?:street|st|road|rd|avenue|ave|lane|ln|drive|dr|boulevard|blvd)\b", 0.86),
)


def detect_regex(text: str) -> list[Candidate]:
    candidates: list[Candidate] = []
    for entity_type, pattern, confidence in PATTERNS:
        for match in re.finditer(pattern, text):
            span = match.span(1) if entity_type in {"BANK_ACCOUNT", "DATE_OF_BIRTH"} else match.span()
            value = text[span[0]:span[1]]
            if entity_type == "CARD" and len(re.sub(r"\D", "", value)) not in range(13, 20):
                continue
            if entity_type == "PHONE" and len(re.sub(r"\D", "", value)) < 7:
                continue
            candidates.append(Candidate(entity_type, span[0], span[1], confidence))
    return candidates
