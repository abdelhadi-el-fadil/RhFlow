"""Compatibility wrapper for legacy imports."""

from app.ai.service.cv.analysis_agents_service import (
    CandidatInfo,
    EvaluationCv,
    ExperienceInfo,
    FormationInfo,
    RecommendationValue,
    evaluate_cv,
    extract_candidat_info,
)

__all__ = [
    "RecommendationValue",
    "FormationInfo",
    "ExperienceInfo",
    "CandidatInfo",
    "EvaluationCv",
    "extract_candidat_info",
    "evaluate_cv",
]
