from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

Decision = str

# Labels exposed by NudeNet's detector.
CRITICAL_EXPLICIT = {
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
}

REVIEW_EXPLICIT = {
    "BUTTOCKS_EXPOSED",
}

BLOCK_THRESHOLD = 0.65
REVIEW_THRESHOLD = 0.30
BUTTOCKS_REVIEW_THRESHOLD = 0.55


@dataclass(frozen=True)
class PolicyResult:
    decision: Decision
    score: float
    reasons: list[str]


def evaluate_detections(detections: Iterable[dict]) -> PolicyResult:
    detections = list(detections)
    if not detections:
        return PolicyResult(decision="ALLOW", score=0.0, reasons=[])

    block_hits: list[tuple[str, float]] = []
    review_hits: list[tuple[str, float]] = []

    for item in detections:
        label = str(item.get("class", ""))
        score = float(item.get("score", 0.0))

        if label in CRITICAL_EXPLICIT:
            if score >= BLOCK_THRESHOLD:
                block_hits.append((label, score))
            elif score >= REVIEW_THRESHOLD:
                review_hits.append((label, score))

        if label in REVIEW_EXPLICIT and score >= BUTTOCKS_REVIEW_THRESHOLD:
            review_hits.append((label, score))

    if block_hits:
        block_hits.sort(key=lambda x: x[1], reverse=True)
        return PolicyResult(
            decision="BLOCK",
            score=block_hits[0][1],
            reasons=[f"{label}:{score:.3f}" for label, score in block_hits[:5]],
        )

    if review_hits:
        review_hits.sort(key=lambda x: x[1], reverse=True)
        return PolicyResult(
            decision="REVIEW",
            score=review_hits[0][1],
            reasons=[f"{label}:{score:.3f}" for label, score in review_hits[:5]],
        )

    return PolicyResult(decision="ALLOW", score=0.0, reasons=[])
