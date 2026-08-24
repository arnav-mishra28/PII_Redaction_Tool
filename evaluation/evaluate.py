import json
from collections import defaultdict
from pathlib import Path

from app.detectors.hybrid import detect_pii


def evaluate(path: Path) -> None:
    counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for item in json.loads(path.read_text()):
        expected = {(start, end, label) for start, end, label in item["entities"]}
        actual = {(entity.start, entity.end, entity.entity_type) for entity in detect_pii(item["text"])}
        for label in {entry[2] for entry in expected | actual}:
            counts[label]["tp"] += len({entry for entry in expected & actual if entry[2] == label})
            counts[label]["fp"] += len({entry for entry in actual - expected if entry[2] == label})
            counts[label]["fn"] += len({entry for entry in expected - actual if entry[2] == label})
    print("category,precision,recall,f1,false_positives,false_negatives")
    for label, value in sorted(counts.items()):
        precision = value["tp"] / (value["tp"] + value["fp"]) if value["tp"] + value["fp"] else 0
        recall = value["tp"] / (value["tp"] + value["fn"]) if value["tp"] + value["fn"] else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        print(f"{label},{precision:.3f},{recall:.3f},{f1:.3f},{value['fp']},{value['fn']}")


if __name__ == "__main__":
    evaluate(Path(__file__).with_name("dataset.json"))
