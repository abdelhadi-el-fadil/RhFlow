from _pytest.monkeypatch import MonkeyPatch

from app.ai.service.cv import analysis_agents_service
from app.ai.service.cv.analysis_agents_service import (
    CandidatInfo,
    EvaluationCv,
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


def test_evaluate_cv_falls_back_on_invalid_llm_payload(
    monkeypatch: MonkeyPatch,
) -> None:
    def _raise_invalid(*args: object, **kwargs: object) -> EvaluationCv:
        raise ValueError(
            "Fallback parsing failed: No JSON object found in fallback response"
        )

    monkeypatch.setattr(analysis_agents_service, "_run_structured_chat", _raise_invalid)

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

    assert 1 <= evaluation.score_matching <= 100
    assert evaluation.recommandation in {
        RecommendationValue.A_CONVOQUER,
        RecommendationValue.A_ETUDIER,
        RecommendationValue.NE_CORRESPOND_PAS,
    }
    assert len(evaluation.points_forts) >= 3
    assert len(evaluation.points_manquants) >= 3
    assert len(evaluation.questions_entretien) >= 3
    assert "mode de secours" in evaluation.justification_ia.lower()


def test_extract_candidat_info_prefers_fast_heuristic_when_contact_and_skills_present(
    monkeypatch: MonkeyPatch,
) -> None:
    def _should_not_be_called(*args: object, **kwargs: object) -> CandidatInfo:
        raise AssertionError("LLM extraction should be skipped for strong heuristic CV")

    monkeypatch.setattr(
        analysis_agents_service,
        "_run_structured_chat",
        _should_not_be_called,
    )

    cv_markdown = (
        "# EL FADIL Abdelhadi\n"
        "Email: abdellhadi.elfadil@gmail.com\n"
        "Telephone: +212 654 099 755\n"
        "Competences: Python, FastAPI, Docker, PostgreSQL, GitHub\n"
    )

    candidate = analysis_agents_service.extract_candidat_info(cv_markdown)

    assert candidate.email == "abdellhadi.elfadil@gmail.com"
    assert candidate.telephone is not None
    assert set(candidate.skills) >= {
        "Python",
        "FastAPI",
        "Docker",
        "PostgreSQL",
        "GitHub",
    }


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
