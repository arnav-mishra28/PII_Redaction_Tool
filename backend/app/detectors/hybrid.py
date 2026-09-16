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
    """Merge candidates from regex and NER, resolving overlaps by confidence.

    When two candidates overlap, the one with higher confidence wins.  Regex
    detections are generally higher-confidence for structured PII, so they
    naturally suppress overlapping NER hits that are likely false positives.
    """
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


def _suppress_ner_near_regex(regex_candidates: list[Candidate],
                             ner_candidates: list[Candidate],
                             text: str) -> list[Candidate]:
    """Remove NER candidates that sit inside the contextual prefix/suffix zone
    of a regex-detected entity.  For example, the word 'Email' right before an
    EMAIL entity, or 'PAN' right before a PAN entity.

    This catches cases where spaCy sees 'Email' or 'PAN' as a PERSON/ORG and
    the overlap resolver can't discard them because they don't technically
    overlap with the regex span.
    """
    if not regex_candidates or not ner_candidates:
        return ner_candidates

    # Build a set of "protected zones" around each regex entity.  The zone
    # extends a few characters before the regex span start (to cover the label
    # word) and after the span end.
    CONTEXT_MARGIN = 15  # characters
    protected: list[tuple[int, int]] = []
    for rc in regex_candidates:
        zone_start = max(0, rc.start - CONTEXT_MARGIN)
        zone_end = min(len(text), rc.end + CONTEXT_MARGIN)
        protected.append((zone_start, zone_end))

    filtered: list[Candidate] = []
    for nc in ner_candidates:
        suppressed = False
        for zone_start, zone_end in protected:
            if nc.start >= zone_start and nc.end <= zone_end:
                suppressed = True
                break
        if not suppressed:
            filtered.append(nc)
    return filtered


def detect_pii(text: str) -> list[Entity]:
    regex_candidates = detect_regex(text)
    ner_candidates = detect_ner(text)
    ner_candidates = _suppress_ner_near_regex(regex_candidates, ner_candidates, text)
    return _merge(regex_candidates + ner_candidates)
