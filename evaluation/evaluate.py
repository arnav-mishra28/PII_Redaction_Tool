import json
from collections import defaultdict
from pathlib import Path

from app.detectors.hybrid import detect_pii


def evaluate(path: Path) -> None:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for item in json.loads(path.read_text()):
        expected = {(start, end, label) for start, end, label in item["entities"]}
        actual = {(entity.start, entity.end, entity.entity_type) for entity in detect_pii(item["text"])}
        for label in {entry[2] for entry in expected | actual}:
            tp = len({entry for entry in expected & actual if entry[2] == label})
            fp = len({entry for entry in actual - expected if entry[2] == label})
            fn = len({entry for entry in expected - actual if entry[2] == label})
            counts[label]["tp"] += tp
            counts[label]["fp"] += fp
            counts[label]["fn"] += fn
            total_tp += tp
            total_fp += fp
            total_fn += fn

    # Header
    print()
    print(f"{'Category':<18} {'Prec':>7} {'Recall':>7} {'F1':>7} {'TP':>5} {'FP':>5} {'FN':>5}")
    print("-" * 62)

    macro_precision = 0.0
    macro_recall = 0.0
    macro_f1 = 0.0
    num_categories = 0

    for label, value in sorted(counts.items()):
        precision = value["tp"] / (value["tp"] + value["fp"]) if value["tp"] + value["fp"] else 0
        recall = value["tp"] / (value["tp"] + value["fn"]) if value["tp"] + value["fn"] else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        print(f"{label:<18} {precision:>7.3f} {recall:>7.3f} {f1:>7.3f} {value['tp']:>5} {value['fp']:>5} {value['fn']:>5}")

        macro_precision += precision
        macro_recall += recall
        macro_f1 += f1
        num_categories += 1

    print("-" * 62)

    # Micro-averaged metrics (pooled TP/FP/FN)
    micro_precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0
    micro_recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if micro_precision + micro_recall else 0
    print(f"{'Micro-avg':<18} {micro_precision:>7.3f} {micro_recall:>7.3f} {micro_f1:>7.3f} {total_tp:>5} {total_fp:>5} {total_fn:>5}")

    # Macro-averaged metrics (average of per-category)
    if num_categories:
        macro_precision /= num_categories
        macro_recall /= num_categories
        macro_f1 /= num_categories
    print(f"{'Macro-avg':<18} {macro_precision:>7.3f} {macro_recall:>7.3f} {macro_f1:>7.3f}")
    print()
    print(f"Total samples: {len(json.loads(path.read_text()))}  |  Categories: {num_categories}  |  Total entities: {total_tp + total_fn}")
    print()


if __name__ == "__main__":
    evaluate(Path(__file__).with_name("dataset.json"))
