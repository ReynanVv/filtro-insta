from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from threading import Lock

import cv2
from nudenet import NudeDetector

from .policy import PolicyResult, evaluate_detections

_detector: NudeDetector | None = None
_detector_lock = Lock()

SAMPLE_EVERY_SECONDS = float(os.getenv("SAMPLE_EVERY_SECONDS", "1.0"))
MAX_VIDEO_SAMPLES = int(os.getenv("MAX_VIDEO_SAMPLES", "120"))
DETECTOR_SCORE_THRESHOLD = float(os.getenv("DETECTOR_SCORE_THRESHOLD", "0.25"))


def get_detector() -> NudeDetector:
    global _detector
    if _detector is None:
        with _detector_lock:
            if _detector is None:
                _detector = NudeDetector()
    return _detector


def _normalize_detection(item: dict, frame_second: float | None = None) -> dict:
    normalized = {
        "class": str(item.get("class", "")),
        "score": round(float(item.get("score", 0.0)), 6),
        "box": [int(v) for v in item.get("box", [])],
    }
    if frame_second is not None:
        normalized["frame_second"] = round(frame_second, 3)
    return normalized


def _aggregate_policy(detections: list[dict]) -> PolicyResult:
    return evaluate_detections(detections)


def moderate_image(data: bytes) -> dict:
    started = time.perf_counter()
    detector = get_detector()
    raw = detector.detect(data, score_threshold=DETECTOR_SCORE_THRESHOLD)
    detections = [_normalize_detection(item) for item in raw]
    policy = _aggregate_policy(detections)

    return {
        "decision": policy.decision,
        "score": round(policy.score, 6),
        "reasons": policy.reasons,
        "detections": detections,
        "sampled_frames": 1,
        "processing_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def moderate_video(data: bytes, suffix: str = ".mp4") -> dict:
    started = time.perf_counter()
    detector = get_detector()
    all_detections: list[dict] = []
    sampled_frames = 0

    suffix = suffix if suffix.startswith(".") and len(suffix) <= 10 else ".mp4"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        temp_path = tmp.name

    try:
        capture = cv2.VideoCapture(temp_path)
        if not capture.isOpened():
            raise ValueError("Não foi possível abrir o vídeo enviado.")

        fps = capture.get(cv2.CAP_PROP_FPS)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if not fps or fps <= 0:
            fps = 30.0

        step = max(1, int(round(fps * SAMPLE_EVERY_SECONDS)))
        frame_indexes = range(0, max(total_frames, 1), step)

        for frame_index in frame_indexes:
            if sampled_frames >= MAX_VIDEO_SAMPLES:
                break

            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                continue

            second = frame_index / fps
            raw = detector.detect(frame, score_threshold=DETECTOR_SCORE_THRESHOLD)
            all_detections.extend(
                _normalize_detection(item, frame_second=second) for item in raw
            )
            sampled_frames += 1

            # Alta confiança de conteúdo explícito: não precisamos decodificar o
            # restante inteiro do vídeo para impedir a publicação.
            policy_now = _aggregate_policy(all_detections)
            if policy_now.decision == "BLOCK" and policy_now.score >= 0.85:
                break

        capture.release()
    finally:
        Path(temp_path).unlink(missing_ok=True)

    policy = _aggregate_policy(all_detections)

    # Mantém o payload pequeno: retornamos primeiro as detecções mais confiáveis.
    all_detections.sort(key=lambda item: item["score"], reverse=True)

    return {
        "decision": policy.decision,
        "score": round(policy.score, 6),
        "reasons": policy.reasons,
        "detections": all_detections[:50],
        "sampled_frames": sampled_frames,
        "processing_ms": round((time.perf_counter() - started) * 1000, 2),
    }
