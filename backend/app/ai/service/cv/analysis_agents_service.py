"""Two independent LLM agents for CV analysis."""

from __future__ import annotations

import json
import re
from enum import Enum
from typing import TypeVar, cast

from pydantic import AliasChoices, BaseModel, Field, model_validator


class RecommendationValue(str, Enum):
    A_CONVOQUER = "A_CONVOQUER"
    A_ETUDIER = "A_ETUDIER"
    NE_CORRESPOND_PAS = "NE_CORRESPOND_PAS"


class FormationInfo(BaseModel):
    titre: str = Field(
        description="Intitule exact de la formation depuis le CV",
        validation_alias=AliasChoices("titre", "degree", "diplome", "formation"),
    )
    date_obtention: str | None = Field(
        default=None,
        description="Date explicite d'obtention; null si absente",
        validation_alias=AliasChoices(
            "date_obtention", "dateObtention", "date", "year"
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_keys(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        return {
            "titre": _pick_first_text(
                data, ("titre", "title", "degree", "diplome", "formation")
            ),
            "date_obtention": _pick_first_text(
                data,
                ("date_obtention", "dateObtention", "date", "year", "start", "end"),
            ),
        }


class ExperienceInfo(BaseModel):
    titre: str = Field(
        description="Intitule du poste/experience depuis le CV",
        validation_alias=AliasChoices("titre", "title", "poste"),
    )
    entreprise: str | None = Field(
        default=None,
        description="Nom de l'entreprise explicite; null si absent",
        validation_alias=AliasChoices("entreprise", "company", "societe"),
    )
    periode: str | None = Field(
        default=None,
        description="Periode explicite telle qu'ecrite dans le CV",
        validation_alias=AliasChoices("periode", "period", "duration"),
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_keys(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        return {
            "titre": _pick_first_text(data, ("titre", "title", "poste", "role")),
            "entreprise": _pick_first_text(
                data, ("entreprise", "company", "societe", "organisation")
            ),
            "periode": _pick_first_text(
                data, ("periode", "period", "duration", "start", "end")
            ),
        }


class CandidatInfo(BaseModel):
    nom: str | None = Field(
        default=None, validation_alias=AliasChoices("nom", "name", "full_name")
    )
    email: str | None = Field(
        default=None, validation_alias=AliasChoices("email", "mail")
    )
    telephone: str | None = Field(
        default=None, validation_alias=AliasChoices("telephone", "phone", "tel")
    )
    formations: list[FormationInfo] = Field(default_factory=list)
    experiences: list[ExperienceInfo] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_payload(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        return _normalize_candidate_payload(data)


class EvaluationCv(BaseModel):
    score_matching: int = Field(ge=1, le=100)
    points_forts: list[str] = Field(min_length=3, max_length=5)
    points_manquants: list[str] = Field(min_length=3, max_length=5)
    recommandation: RecommendationValue
    justification_ia: str
    questions_entretien: list[str] = Field(min_length=3, max_length=5)

    @model_validator(mode="before")
    @classmethod
    def _normalize_payload(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        return _normalize_evaluation_payload(data)


EXTRACTION_SYSTEM_PROMPT = """Tu extrais les informations d'un CV.

Regles:
- Utiliser uniquement les informations explicitement presentes dans le CV.
- Ne jamais inventer, deduire ou completer une information absente.
- Retourner null pour une valeur scalaire absente/ambigue.
- Retourner une liste vide s'il n'y a aucune formation ou experience.
- Retourner une liste vide s'il n'y a aucune competence explicite.
- Preserver l'ordre des formations et experiences tel qu'il apparait dans le CV.
- Pour les formations, extraire le diplome ou l'intitule le plus precis disponible.
- Pour les experiences, extraire le poste puis l'entreprise
    et la periode si elles sont ecrites.
- Pour les competences, retourner des libelles courts, concrets et deduplices.
- Respecter strictement le schema de sortie fourni."""


EVALUATION_SYSTEM_PROMPT = """Tu es un expert RH senior specialise
dans l'evaluation de candidatures.
Tu analyses avec precision la correspondance entre un CV et une fiche de poste complete.

TON ROLE :
Evaluer objectivement si le profil du candidat repond aux exigences du poste,
en t'appuyant EXCLUSIVEMENT sur les informations fournies dans le CV et la fiche.

SCORE (0-100) :
Attribue un score refletant precisement le niveau de correspondance global.

RECOMMANDATION (valeur EXACTE, sans variation) :
Choisis UNE valeur parmi ces trois uniquement, coherente avec ton score :
- \"A_CONVOQUER\"       : profil bien aligne, entretien vivement recommande
- \"A_ETUDIER\"         : profil interessant mais incomplet, a examiner davantage
- \"NE_CORRESPOND_PAS\" : profil trop eloigne des exigences, ne pas donner suite

POINTS FORTS (3 a 5 elements) :
Identifie les atouts CONCRETS du candidat en rapport avec les exigences de la fiche.

POINTS MANQUANTS (3 a 5 elements) :
Si le profil est excellent, formule des points d'attention mineurs.

JUSTIFICATION (2 a 3 phrases) :
Redige une synthese argumentee a destination du DRH :
explique le score, la recommandation, et ce qui distingue ce candidat.
Sois precis, professionnel et utile pour la decision finale.

QUESTIONS D'ENTRETIEN (3 a 5 questions) :
Genere des questions ciblees pour approfondir les points cles identifies.
Formule chaque question de facon directe et professionnelle.

REGLES ABSOLUES :
1. Baser l'analyse UNIQUEMENT sur le contenu du CV et de la fiche fournis.
2. Ne jamais inventer des competences ou experiences non mentionnees.
3. Le champ recommandation doit etre EXACTEMENT l'une des 3 valeurs ci-dessus.
4. Le score doit etre coherent avec la recommandation choisie.
5. Repondre en francais, ton professionnel.
6. Respecter strictement le schema de sortie fourni."""


ModelT = TypeVar("ModelT", bound=BaseModel)


def _run_structured_chat(
    output_cls: type[ModelT],
    system_prompt: str,
    user_prompt: str,
) -> ModelT:
    from llama_index.core.llms import ChatMessage, MessageRole

    from app.ai.providers.llm.runtime import llm

    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
        ChatMessage(role=MessageRole.USER, content=user_prompt),
    ]

    try:
        structured_llm = llm.as_structured_llm(output_cls=output_cls)
        response = structured_llm.chat(messages)
    except Exception as exc:
        # Some providers (or gateways) reject tool-based structured calls.
        # Fallback: JSON-schema constrained prompt + strict Pydantic validation.
        error_message = str(exc).lower()
        if "tool_choice" not in error_message and "tools" not in error_message:
            raise
        return _run_json_schema_fallback(output_cls, system_prompt, user_prompt)

    if isinstance(response, output_cls):
        return response

    raw = getattr(response, "raw", None)
    if isinstance(raw, output_cls):
        return raw

    message = getattr(response, "message", None)
    content = getattr(message, "content", None) if message is not None else None

    if isinstance(content, str) and content.strip():
        try:
            return output_cls.model_validate_json(content)
        except Exception:
            data = _extract_json_object(content)
            return output_cls.model_validate(data)
    if isinstance(content, dict):
        return output_cls.model_validate(content)

    raise ValueError("Structured output could not be parsed from model response")


def _extract_json_object(text: str) -> dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        loaded = json.loads(cleaned)
        if isinstance(loaded, dict):
            return cast(dict[str, object], loaded)
        raise ValueError("JSON payload is not an object")

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match is None:
        raise ValueError("No JSON object found in fallback response")
    loaded = json.loads(match.group(0))
    if isinstance(loaded, dict):
        return cast(dict[str, object], loaded)
    raise ValueError("JSON payload is not an object")


def _run_json_schema_fallback(
    output_cls: type[ModelT],
    system_prompt: str,
    user_prompt: str,
) -> ModelT:
    from llama_index.core.llms import ChatMessage, MessageRole

    from app.ai.providers.llm.runtime import llm

    schema = json.dumps(output_cls.model_json_schema(), ensure_ascii=True)
    fallback_system = (
        f"{system_prompt}\n\n"
        "Contraintes de sortie:\n"
        "- Retourne uniquement un objet JSON valide.\n"
        "- Respecte strictement ce schema JSON.\n"
        f"Schema: {schema}"
    )

    response = llm.chat(
        [
            ChatMessage(role=MessageRole.SYSTEM, content=fallback_system),
            ChatMessage(role=MessageRole.USER, content=user_prompt),
        ]
    )
    message = response.message
    content = message.content if message is not None else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Fallback response is empty")

    data = _extract_json_object(content)
    return output_cls.model_validate(data)


def _pick_first_text(data: dict[str, object], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _find_first_text_by_keys(payload: object, keys: tuple[str, ...]) -> str | None:
    if isinstance(payload, dict):
        direct = _pick_first_text(payload, keys)
        if direct:
            return direct
        for value in payload.values():
            nested = _find_first_text_by_keys(value, keys)
            if nested:
                return nested
    elif isinstance(payload, list):
        for item in payload:
            nested = _find_first_text_by_keys(item, keys)
            if nested:
                return nested
    return None


def _find_first_list_by_keys(
    payload: object, keys: tuple[str, ...]
) -> list[object] | None:
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for value in payload.values():
            nested = _find_first_list_by_keys(value, keys)
            if nested is not None:
                return nested
    elif isinstance(payload, list):
        for item in payload:
            nested = _find_first_list_by_keys(item, keys)
            if nested is not None:
                return nested
    return None


def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _string_list_from_value(value: object) -> list[str]:
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip(" -\t\n\r")
                if cleaned:
                    output.append(cleaned)
        return output
    if isinstance(value, str):
        lines = [part.strip(" -\t\n\r") for part in re.split(r"\n+|[;•]", value)]
        return [line for line in lines if line]
    return []


def _extract_score(value: object) -> int | None:
    if isinstance(value, int):
        return max(0, min(100, value))
    if isinstance(value, float):
        return max(0, min(100, int(round(value))))
    if isinstance(value, str):
        match = re.search(r"\d{1,3}", value)
        if match:
            return max(0, min(100, int(match.group(0))))
    return None


def _normalize_recommendation(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().upper()
    normalized = _normalized_key(raw)
    mapping = {
        "aconvoquer": "A_CONVOQUER",
        "aetudier": "A_ETUDIER",
        "analyser": "A_ETUDIER",
        "necorrespondpas": "NE_CORRESPOND_PAS",
        "nerepondpas": "NE_CORRESPOND_PAS",
    }
    if raw in {"A_CONVOQUER", "A_ETUDIER", "NE_CORRESPOND_PAS"}:
        return raw
    return mapping.get(normalized)


def _normalize_evaluation_payload(raw: dict[str, object]) -> dict[str, object]:
    normalized_map: dict[str, object] = {}
    for key, value in raw.items():
        normalized_map[_normalized_key(key)] = value

    score = _extract_score(normalized_map.get("scorematching"))
    if score is None:
        score = _extract_score(normalized_map.get("score"))

    points_forts = _string_list_from_value(
        normalized_map.get("pointsforts")
        if "pointsforts" in normalized_map
        else normalized_map.get("atouts")
    )
    points_manquants = _string_list_from_value(
        normalized_map.get("pointsmanquants")
        if "pointsmanquants" in normalized_map
        else normalized_map.get("faiblesses")
    )
    questions = _string_list_from_value(
        normalized_map.get("questionsentretien")
        if "questionsentretien" in normalized_map
        else normalized_map.get("questions")
    )

    recommandation = _normalize_recommendation(
        normalized_map.get("recommandation")
        if "recommandation" in normalized_map
        else normalized_map.get("recommendation")
    )

    justification_value = normalized_map.get("justificationia")
    if not isinstance(justification_value, str) or not justification_value.strip():
        justification_value = normalized_map.get("justification")
    justification = (
        justification_value.strip() if isinstance(justification_value, str) else ""
    )

    output: dict[str, object] = {
        "score_matching": score if score is not None else 0,
        "points_forts": points_forts,
        "points_manquants": points_manquants,
        "recommandation": recommandation,
        "justification_ia": justification,
        "questions_entretien": questions,
    }
    return output


def _normalize_candidate_payload(raw: dict[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {
        "nom": _find_first_text_by_keys(
            raw, ("nom", "name", "full_name", "candidate_name")
        ),
        "email": _find_first_text_by_keys(raw, ("email", "mail", "courriel")),
        "telephone": _find_first_text_by_keys(
            raw, ("telephone", "téléphone", "phone", "tel", "mobile")
        ),
    }

    formations: list[dict[str, object]] = []
    raw_formations = _find_first_list_by_keys(
        raw, ("formations", "education", "educations", "degrees")
    )
    if isinstance(raw_formations, list):
        for item in raw_formations:
            if not isinstance(item, dict):
                continue
            titre = _pick_first_text(
                item, ("titre", "title", "degree", "diplome", "formation")
            )
            if titre is None:
                continue
            formations.append(
                {
                    "titre": titre,
                    "date_obtention": _pick_first_text(
                        item,
                        (
                            "date_obtention",
                            "dateObtention",
                            "date",
                            "year",
                            "start",
                            "end",
                        ),
                    ),
                }
            )

    experiences: list[dict[str, object]] = []
    raw_experiences = _find_first_list_by_keys(
        raw, ("experiences", "experience", "work_experience", "jobs")
    )
    if isinstance(raw_experiences, list):
        for item in raw_experiences:
            if not isinstance(item, dict):
                continue
            titre = _pick_first_text(
                item, ("titre", "title", "poste", "role", "position")
            )
            if titre is None:
                continue
            experiences.append(
                {
                    "titre": titre,
                    "entreprise": _pick_first_text(
                        item, ("entreprise", "company", "societe", "organisation")
                    ),
                    "periode": _pick_first_text(
                        item, ("periode", "period", "duration", "start", "end")
                    ),
                }
            )

    skills = _string_list_from_value(
        _find_first_list_by_keys(
            raw,
            ("skills", "competences", "competencies", "technical_skills", "stack"),
        )
        or _find_first_text_by_keys(
            raw,
            ("skills", "competences", "competencies", "technical_skills", "stack"),
        )
    )
    deduped_skills: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        token = _normalized_key(skill)
        if not token or token in seen:
            continue
        seen.add(token)
        deduped_skills.append(skill)

    normalized["formations"] = formations
    normalized["experiences"] = experiences
    normalized["skills"] = deduped_skills
    return normalized


def _extract_email_from_text(text: str) -> str | None:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def _extract_phone_from_text(text: str) -> str | None:
    preferred_lines = [
        line
        for line in text.splitlines()
        if re.search(
            r"\b(?:tel|telephone|téléphone|mobile|gsm|contact)\b",
            line,
            flags=re.IGNORECASE,
        )
    ]

    if preferred_lines:
        preferred_text = "\n".join(preferred_lines)
        phone = _extract_phone_from_text_from_candidates(preferred_text)
        if phone:
            return phone

    return _extract_phone_from_text_from_candidates(text)


def _extract_phone_from_text_from_candidates(text: str) -> str | None:
    candidates: list[str] = re.findall(r"(?:\+?\d[\d\s().\-/]{7,}\d)", text)
    for candidate in candidates:
        normalized: str = candidate.strip()
        digits = re.sub(r"\D", "", normalized)
        if len(digits) < 8 or len(digits) > 15:
            continue
        if re.fullmatch(r"(?:19|20)\d{2}", digits):
            continue
        if re.fullmatch(r"(?:19|20)\d{2}(?:19|20)\d{2}", digits):
            continue
        if re.search(r"\b(?:19|20)\d{2}\s*[-/]\s*(?:19|20)\d{2}\b", normalized):
            continue
        if re.search(r"\b(?:0?[1-9]|1[0-2])\s*[-/]\s*(?:19|20)\d{2}\b", normalized):
            continue
        if (
            re.search(r"\b(?:19|20)\d{2}\b", normalized)
            and len(digits) <= 10
            and "/" in normalized
        ):
            continue
        return normalized
    return None


def _extract_name_from_text(text: str) -> str | None:
    lines = [line.strip(" #-\t") for line in text.splitlines()]
    blockers = ("email", "mail", "tel", "phone", "cv", "experience", "formation")
    for line in lines:
        if not line:
            continue
        lower = line.lower()
        if any(token in lower for token in blockers):
            continue
        if len(line.split()) < 2:
            continue
        if any(ch.isdigit() for ch in line):
            continue
        return line[:120]
    return None


def _derive_name_from_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local = email.split("@", maxsplit=1)[0]
    candidate = re.sub(r"[._-]+", " ", local).strip()
    if len(candidate.split()) < 2:
        return None
    return " ".join(part.capitalize() for part in candidate.split())


def _sanitize_email(value: str | None) -> str | None:
    if not value:
        return None
    email = value.strip().strip('<>()[]{};,."')
    if re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email):
        return email
    return None


def _sanitize_phone(value: str | None) -> str | None:
    if not value:
        return None
    compact = value.strip()
    if re.fullmatch(r"(?:19|20)\d{2}\s*[-/]\s*(?:19|20)\d{2}", compact):
        return None
    if re.fullmatch(r"(?:19|20)\d{2}", compact):
        return None
    return _extract_phone_from_text(compact)


def sanitize_candidate_identity(
    nom: str | None,
    email: str | None,
    telephone: str | None,
    cv_markdown: str,
) -> tuple[str | None, str | None, str | None]:
    safe_email = _sanitize_email(email) or _extract_email_from_text(cv_markdown)
    safe_phone = _sanitize_phone(telephone) or _extract_phone_from_text(cv_markdown)

    safe_nom = nom.strip()[:120] if nom and nom.strip() else None
    if not safe_nom:
        safe_nom = _extract_name_from_text(cv_markdown)
    if not safe_nom:
        safe_nom = _derive_name_from_email(safe_email)

    return safe_nom, safe_email, safe_phone


def _post_validate_candidate(candidate: CandidatInfo, cv_markdown: str) -> CandidatInfo:
    candidate.nom, candidate.email, candidate.telephone = sanitize_candidate_identity(
        candidate.nom,
        candidate.email,
        candidate.telephone,
        cv_markdown,
    )

    candidate.formations = [
        f for f in candidate.formations if f.titre and f.titre.strip()
    ]
    candidate.experiences = [
        e for e in candidate.experiences if e.titre and e.titre.strip()
    ]
    normalized_skills: list[str] = []
    seen: set[str] = set()
    for skill in candidate.skills:
        cleaned = skill.strip(" -\t\n\r")
        token = _normalized_key(cleaned)
        if not cleaned or not token or token in seen:
            continue
        seen.add(token)
        normalized_skills.append(cleaned)
    candidate.skills = normalized_skills
    return candidate


def extract_candidat_info(cv_markdown: str) -> CandidatInfo:
    """Agent 1 - Extract candidate information from CV markdown."""
    user_prompt = (
        f"CV (Markdown brut, conserve tel quel):\n```markdown\n{cv_markdown}\n```"
    )
    candidate = _run_structured_chat(
        CandidatInfo, EXTRACTION_SYSTEM_PROMPT, user_prompt
    )
    return _post_validate_candidate(candidate, cv_markdown)


def evaluate_cv(
    fiche_de_poste: str,
    cv_markdown: str,
) -> EvaluationCv:
    """Agent 2 - Evaluate CV against project job description context.

    Evaluates directly against the full CV markdown rather than the
    (lossy) profile extracted by agent 1, so an incomplete or wrong
    extraction cannot silently bias the score. Agent 1's output is used
    only for persistence/display, never as an input here.
    """
    user_prompt = (
        "Evalue la correspondance entre ce candidat et cette fiche de poste.\n\n"
        f"CONTEXTE DU POSTE :\n{fiche_de_poste}\n\n"
        "CV DU CANDIDAT (Markdown brut, source unique et complete pour "
        "l'analyse) :\n"
        f"{cv_markdown}"
    )
    return _run_structured_chat(EvaluationCv, EVALUATION_SYSTEM_PROMPT, user_prompt)
