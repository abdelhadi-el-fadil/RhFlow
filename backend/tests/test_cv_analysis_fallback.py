import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from app.ai.service.cv import analysis_agents_service
from app.ai.service.cv.analysis_agents_service import (
    CandidatInfo,
    EvaluationCv,
    ExperienceInfo,
    FormationInfo,
    RecommendationValue,
)


def test_extract_candidat_info_falls_back_on_invalid_llm_payload(
    monkeypatch: MonkeyPatch,
) -> None:
    def _raise_invalid(*args: object, **kwargs: object) -> CandidatInfo:
        raise ValueError(
            "Fallback parsing failed: No JSON object found in fallback response"
        )

    monkeypatch.setattr(analysis_agents_service, "_run_structured_chat", _raise_invalid)

    cv_markdown = (
        "# EL FADIL Abdelhadi\n"
        "Email: Abdellhadi.elfadil@gmail.com\n"
        "Tel: +212 654 099 755\n"
        "Competences: Python, FastAPI, Docker\n"
    )

    candidate = analysis_agents_service.extract_candidat_info(cv_markdown)

    assert candidate.email == "Abdellhadi.elfadil@gmail.com"
    assert candidate.telephone is not None
    assert candidate.nom is not None
    assert len(candidate.skills) >= 1


def test_evaluate_cv_retries_until_it_gets_seven_llm_questions(
    monkeypatch: MonkeyPatch,
) -> None:
    attempts = {"count": 0}

    def _fake_run(*args: object, **kwargs: object) -> EvaluationCv:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return EvaluationCv.model_validate(
                {
                    "score_matching": 82,
                    "points_forts": ["Python", "FastAPI", "LLM"],
                    "points_manquants": ["MLOps", "Docker", "Kubernetes"],
                    "recommandation": "A_CONVOQUER",
                    "justification_ia": "Profil solide.",
                    "questions_entretien": [
                        "Question 1 ?",
                        "Question 2 ?",
                        "Question 3 ?",
                    ],
                }
            )
        return EvaluationCv(
            score_matching=82,
            points_forts=["Python", "FastAPI", "LLM"],
            points_manquants=["MLOps", "Docker", "Kubernetes"],
            recommandation=RecommendationValue.A_CONVOQUER,
            justification_ia="Profil solide et bien aligne avec le poste.",
            questions_entretien=[
                (
                    "Comment avez-vous concu votre pipeline d'extraction CV le "
                    "plus abouti ?"
                ),
                "Comment validez-vous la fiabilite des sorties structurees d'un LLM ?",
                (
                    "Quelles decisions d'architecture FastAPI avez-vous prises "
                    "sur un projet recent ?"
                ),
                (
                    "Comment gerez-vous les erreurs de parsing dans une chaine de "
                    "traitement documentaire ?"
                ),
                "Quel projet illustre le mieux votre maitrise de Python pour l'IA ?",
                "Comment mesurez-vous la qualite d'une evaluation candidat-poste ?",
                "Quelle experience avez-vous de la mise en production d'agents LLM ?",
            ],
        )

    monkeypatch.setattr(analysis_agents_service, "_run_structured_chat", _fake_run)

    fiche_de_poste = (
        "Titre du poste: Ingenieur IA\n"
        "Competences techniques: Python, FastAPI, Docker, PostgreSQL\n"
    )
    cv_markdown = (
        "# CV\n"
        "Experience Python et FastAPI\n"
        "Competences: Python, FastAPI, Git\n"
    )

    evaluation = analysis_agents_service.evaluate_cv(fiche_de_poste, cv_markdown)

    assert attempts["count"] == 2
    assert len(evaluation.questions_entretien) == 7
    assert evaluation.questions_entretien[0].startswith("Comment")


def test_evaluate_cv_reraises_infrastructure_errors(
    monkeypatch: MonkeyPatch,
) -> None:
    def _raise_auth_error(*args: object, **kwargs: object) -> EvaluationCv:
        raise RuntimeError("401 Unauthorized: invalid API key")

    monkeypatch.setattr(
        analysis_agents_service,
        "_run_structured_chat",
        _raise_auth_error,
    )

    with pytest.raises(RuntimeError, match="401 Unauthorized"):
        analysis_agents_service.evaluate_cv(
            "Titre du poste: Ingenieur IA",
            "# CV\nAlice Dupont\nPython\nFastAPI",
        )


def test_evaluate_cv_does_not_retry_provider_timeouts(
    monkeypatch: MonkeyPatch,
) -> None:
    attempts = {"count": 0}

    def _raise_timeout(*args: object, **kwargs: object) -> EvaluationCv:
        attempts["count"] += 1
        raise TimeoutError("Read timed out")

    monkeypatch.setattr(
        analysis_agents_service,
        "_run_structured_chat",
        _raise_timeout,
    )

    with pytest.raises(TimeoutError, match="timed out on attempt 1/3"):
        analysis_agents_service.evaluate_cv(
            "Titre du poste: Ingenieur IA",
            "# CV\nAlice Dupont\nPython\nFastAPI",
        )

    assert attempts["count"] == 1


def test_extract_candidat_info_uses_llm_even_when_contact_and_skills_present(
    monkeypatch: MonkeyPatch,
) -> None:
    calls = {"count": 0}

    def _fake_run(*args: object, **kwargs: object) -> CandidatInfo:
        calls["count"] += 1
        return CandidatInfo.model_construct(
            nom="EL FADIL Abdelhadi",
            email="abdellhadi.elfadil@gmail.com",
            telephone="+212 654 099 755",
            formations=[
                FormationInfo(titre="Master Data Science", date_obtention="2023"),
                FormationInfo(titre="Licence Informatique", date_obtention="2021"),
            ],
            experiences=[
                ExperienceInfo(
                    titre="Ingenieur IA",
                    entreprise="STAPORT",
                    periode="2023-2026",
                )
            ],
            skills=["Python", "FastAPI", "Docker"],
        )

    monkeypatch.setattr(
        analysis_agents_service,
        "_run_structured_chat",
        _fake_run,
    )

    cv_markdown = (
        "# EL FADIL Abdelhadi\n"
        "Email: abdellhadi.elfadil@gmail.com\n"
        "Telephone: +212 654 099 755\n"
        "Formation: Master Data Science - 2023\n"
        "Experience: Ingenieur IA - STAPORT - 2023-2026\n"
        "Competences: Python, FastAPI, Docker, PostgreSQL, GitHub\n"
    )

    candidate = analysis_agents_service.extract_candidat_info(cv_markdown)

    assert calls["count"] == 1
    assert candidate.email == "abdellhadi.elfadil@gmail.com"
    assert candidate.telephone is not None
    assert [item.titre for item in candidate.formations] == [
        "Master Data Science",
        "Licence Informatique",
    ]
    assert candidate.experiences[0].titre == "Ingenieur IA"
    assert candidate.experiences[0].entreprise == "STAPORT"
    assert set(candidate.skills) >= {
        "Python",
        "FastAPI",
        "Docker",
        "PostgreSQL",
        "GitHub",
    }


def test_extract_candidat_info_falls_back_only_after_repeated_invalid_llm_payloads(
    monkeypatch: MonkeyPatch,
) -> None:
    attempts = {"count": 0}

    def _raise_invalid(*args: object, **kwargs: object) -> CandidatInfo:
        attempts["count"] += 1
        raise ValueError(
            "Fallback parsing failed: No JSON object found in fallback response"
        )

    monkeypatch.setattr(analysis_agents_service, "_run_structured_chat", _raise_invalid)

    cv_markdown = (
        "# EL FADIL Abdelhadi\n"
        "Email: Abdellhadi.elfadil@gmail.com\n"
        "Tel: +212 654 099 755\n"
        "Competences: Python, FastAPI, Docker\n"
    )

    candidate = analysis_agents_service.extract_candidat_info(cv_markdown)

    assert attempts["count"] == 3
    assert candidate.email == "Abdellhadi.elfadil@gmail.com"
    assert candidate.telephone is not None
    assert candidate.nom is not None
    assert len(candidate.skills) >= 1


def test_extract_candidat_info_stops_when_retry_budget_is_exhausted(
    monkeypatch: MonkeyPatch,
) -> None:
    attempts = {"count": 0}
    remaining_budget_values = iter([60.0, 25.0])

    def _fake_remaining_budget(_started_at: float) -> float:
        return next(remaining_budget_values)

    def _raise_invalid(*args: object, **kwargs: object) -> CandidatInfo:
        attempts["count"] += 1
        raise ValueError(
            "Fallback parsing failed: No JSON object found in fallback response"
        )

    monkeypatch.setattr(
        analysis_agents_service,
        "_remaining_retry_budget_seconds",
        _fake_remaining_budget,
    )
    monkeypatch.setattr(analysis_agents_service, "_run_structured_chat", _raise_invalid)

    with pytest.raises(TimeoutError, match="exhausted retry budget after 1 attempt"):
        analysis_agents_service.extract_candidat_info(
            "# CV\nAlice Dupont\nEmail: alice@example.com\nPython"
        )

    assert attempts["count"] == 1


def test_extract_candidat_info_reraises_infrastructure_errors(
    monkeypatch: MonkeyPatch,
) -> None:
    def _raise_rate_limit(*args: object, **kwargs: object) -> CandidatInfo:
        raise RuntimeError("429 Too Many Requests")

    monkeypatch.setattr(
        analysis_agents_service,
        "_run_structured_chat",
        _raise_rate_limit,
    )

    with pytest.raises(RuntimeError, match="429 Too Many Requests"):
        analysis_agents_service.extract_candidat_info(
            "# CV\nAlice Dupont\nEmail: alice@example.com\nPython"
        )


def test_extract_skills_filters_noise_and_keeps_technologies() -> None:
    cv_markdown = (
        "## Competences techniques\n"
        "Java, Python, C, PHP, HTML5, CSS3, JavaScript, SQL, Oracle, "
        "MySQL, PostgreSQL, Docker, GitHub\n"
        "## Langues\n"
        "Arabe: maternelle | Francais: professionnel | Anglais: professionnel\n"
    )

    skills = analysis_agents_service._extract_skills_from_cv_markdown(cv_markdown)

    assert "Python" in skills
    assert "Docker" in skills
    assert "PostgreSQL" in skills
    assert "GitHub" in skills
    assert all("professionnel" not in skill.lower() for skill in skills)
    assert all("maternelle" not in skill.lower() for skill in skills)


def test_extract_score_logs_when_value_is_clamped(
    caplog: LogCaptureFixture,
) -> None:
    with caplog.at_level("WARNING"):
        score = analysis_agents_service._extract_score("120")

    assert score == 100
    assert "Clamped LLM evaluation score" in caplog.text


def test_normalize_candidate_payload_logs_dropped_entries(
    caplog: LogCaptureFixture,
) -> None:
    payload = {
        "formations": [
            {"title": "Master IA", "year": "2024"},
            "invalid formation",
            {"year": "2022"},
        ],
        "experiences": [
            {"title": "ML Engineer", "company": "ACME"},
            42,
            {"company": "Missing title corp"},
        ],
        "skills": ["Python"],
    }

    with caplog.at_level("WARNING"):
        normalized = analysis_agents_service._normalize_candidate_payload(payload)

    assert normalized["formations"] == [
        {"titre": "Master IA", "date_obtention": "2024"}
    ]
    assert normalized["experiences"] == [
        {
            "titre": "ML Engineer",
            "entreprise": "ACME",
            "periode": None,
        }
    ]
    assert "Dropping malformed candidate formation entry" in caplog.text
    assert "Dropping malformed candidate experience entry" in caplog.text
