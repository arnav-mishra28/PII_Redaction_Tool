from app.detectors.hybrid import detect_pii
from app.redaction.service import redact_text


def test_hybrid_detects_structured_pii_without_values_in_entities():
    text = "Email synthetic.user@example.test, PAN ABCDE1234F, IP 192.168.1.10"
    entities = detect_pii(text)
    assert {entity.entity_type for entity in entities} >= {"EMAIL", "PAN", "IP_ADDRESS"}
    assert all(not hasattr(entity, "value") for entity in entities)


def test_overlap_prefers_higher_confidence_candidate():
    text = "Reach synthetic.user@example.test"
    entities = detect_pii(text)
    email = next(entity for entity in entities if entity.entity_type == "EMAIL")
    assert text[email.start:email.end] == "synthetic.user@example.test"
    assert len(entities) == 1


def test_redaction_modes():
    text = "Contact synthetic.user@example.test"
    entity = next(entity for entity in detect_pii(text) if entity.entity_type == "EMAIL")
    assert redact_text(text, [entity]) == "Contact [REDACTED_EMAIL]"
    assert "synthetic.user@example.test" not in redact_text(text, [entity], "black")
    assert redact_text(text, [entity], "partial").startswith("Contact synt")
