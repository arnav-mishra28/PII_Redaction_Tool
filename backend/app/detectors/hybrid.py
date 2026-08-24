from .ner_detector import detect_ner
from .regex_detector import Candidate, detect_regex
from app.models.schemas import DetectionMethod, Entity, RiskLevel


RISK: dict[str, RiskLevel] = {
    "CARD": RiskLevel.CRITICAL, "AADHAAR": RiskLevel.CRITICAL, "PAN": RiskLevel.HIGH,
    "BANK_ACCOUNT": RiskLevel.HIGH, "EMAIL": RiskLevel.HIGH, "PHONE": RiskLevel.HIGH,
    "IFSC": RiskLevel.HIGH, "DATE_OF_BIRTH": RiskLevel.MEDIUM, "PERSON": RiskLevel.MEDIUM,
    "ADDRESS": RiskLevel.MEDIUM, "LOCATION": RiskLevel.LOW, "ORGANIZATION": RiskLevel.LOW,
    "IP_ADDRESS": RiskLevel.MEDIUM, "SOCIAL_HANDLE": RiskLevel.MEDIUM,
}


def _merge(candidates: list[Candidate]) -> list[Entity]:
    chosen: list[Candidate] = []
    for candidate in sorted(candidates, key=lambda item: (item.start, -(item.end - item.start), -item.confidence)):
        overlaps = [item for item in chosen if item.start < candidate.end and candidate.start < item.end]
        if not overlaps:
            chosen.append(candidate)
        elif candidate.confidence > max(item.confidence for item in overlaps):
            chosen = [item for item in chosen if item not in overlaps]
            chosen.append(candidate)
    return [Entity(entity_type=item.entity_type, start=item.start, end=item.end, confidence=item.confidence,
                   detection_method=DetectionMethod(item.method), risk_level=RISK.get(item.entity_type, RiskLevel.MEDIUM))
            for item in sorted(chosen, key=lambda item: item.start)]


def detect_pii(text: str) -> list[Entity]:
    return _merge(detect_regex(text) + detect_ner(text))
