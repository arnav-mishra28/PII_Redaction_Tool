from app.models.schemas import Entity


def _replacement(entity: Entity, value: str, mode: str) -> str:
    if mode == "black":
        return "█" * max(len(value), 1)
    if mode == "partial":
        keep = max(1, min(4, len(value) // 3))
        return value[:keep] + "*" * max(len(value) - keep, 1)
    return f"[REDACTED_{entity.entity_type}]"


def redact_text(text: str, entities: list[Entity], mode: str = "typed") -> str:
    for entity in sorted(entities, key=lambda item: item.start, reverse=True):
        text = text[:entity.start] + _replacement(entity, text[entity.start:entity.end], mode) + text[entity.end:]
    return text
