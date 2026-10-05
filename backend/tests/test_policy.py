from app.policy import evaluate_detections


def test_allows_when_no_explicit_detection():
    result = evaluate_detections(
        [
            {"class": "FACE_FEMALE", "score": 0.99},
            {"class": "BELLY_EXPOSED", "score": 0.95},
        ]
    )
    assert result.decision == "ALLOW"


def test_blocks_high_confidence_exposed_breast():
    result = evaluate_detections(
        [{"class": "FEMALE_BREAST_EXPOSED", "score": 0.91}]
    )
    assert result.decision == "BLOCK"
    assert result.score == 0.91


def test_sends_borderline_explicit_content_to_review():
    result = evaluate_detections(
        [{"class": "FEMALE_GENITALIA_EXPOSED", "score": 0.48}]
    )
    assert result.decision == "REVIEW"


def test_sends_exposed_buttocks_to_review():
    result = evaluate_detections(
        [{"class": "BUTTOCKS_EXPOSED", "score": 0.77}]
    )
    assert result.decision == "REVIEW"
