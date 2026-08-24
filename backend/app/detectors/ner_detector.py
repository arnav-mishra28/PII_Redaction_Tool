from .regex_detector import Candidate


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
        mapping = {"PERSON": ("PERSON", 0.82), "GPE": ("LOCATION", 0.78), "LOC": ("LOCATION", 0.76), "ORG": ("ORGANIZATION", 0.76)}
        return [Candidate(mapping[label][0], ent.start_char, ent.end_char, mapping[label][1], "ner") for ent in doc.ents if ent.label_ in mapping]
    except (ImportError, ValueError):
        return []
