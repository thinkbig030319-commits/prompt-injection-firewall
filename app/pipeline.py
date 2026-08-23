"""
Combines all three detection layers (heuristics, ML classifier,
semantic similarity) into one verdict.
"""
import os
from dataclasses import dataclass, field

import joblib

from app.heuristics import check_heuristics
from app.semantic import check_semantic_similarity

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "classifier.joblib")

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


@dataclass
class FirewallResult:
    text: str
    heuristic_score: float
    ml_score: float
    semantic_score: float
    risk_score: float
    verdict: str
    reasons: list = field(default_factory=list)


BLOCK_THRESHOLD = 0.75
FLAG_THRESHOLD = 0.40
AGREEMENT_THRESHOLD = 0.4


def evaluate_prompt(text: str) -> FirewallResult:
    heuristic_result = check_heuristics(text)

    model = _get_model()
    ml_proba = model.predict_proba([text])[0]
    ml_score = float(ml_proba[1])

    semantic_result = check_semantic_similarity(text)
    semantic_score = semantic_result.score

    scores = [heuristic_result.score, ml_score, semantic_score]

    base_score = max(scores)
    agreeing_layers = sum(1 for s in scores if s >= AGREEMENT_THRESHOLD)
    agreement_boost = {0: 0.0, 1: 0.0, 2: 0.12, 3: 0.22}[agreeing_layers]
    risk_score = round(min(base_score + agreement_boost, 1.0), 4)

    if risk_score >= BLOCK_THRESHOLD:
        verdict = "block"
    elif risk_score >= FLAG_THRESHOLD:
        verdict = "flag"
    else:
        verdict = "allow"

    reasons = list(heuristic_result.triggered_rules)
    if ml_score >= 0.5:
        reasons.append(f"ml_classifier (confidence={ml_score:.2f})")
    if semantic_score >= 0.35:
        reasons.append(f"semantic_similarity (score={semantic_score:.2f}, closest_intent=\"{semantic_result.closest_intent}\")")

    return FirewallResult(
        text=text,
        heuristic_score=round(heuristic_result.score, 4),
        ml_score=round(ml_score, 4),
        semantic_score=round(semantic_score, 4),
        risk_score=risk_score,
        verdict=verdict,
        reasons=reasons,
    )
