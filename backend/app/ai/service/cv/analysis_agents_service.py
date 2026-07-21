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

SKILL_SECTION_KEYS = {
    "skills",
    "skill",
    "competences",
    "competence",
    "competencestechniques",
    "stack",
    "technologies",
    "outilsettechnologies",
}
SKILL_STOP_TITLES = {
    "langues",
    "langue",
    "experiences",
    "experience",
    "formations",
    "formation",
    "education",
    "contact",
    "profil",
}
SKILL_NOISE_TOKENS = {
    "langues",
    "langue",
    "maternelle",
    "professionnel",
    "professionnelle",
    "niveau",
    "email",
    "telephone",
    "tel",
    "contact",
    "adresse",
}
TECH_TOKEN_PATTERN = re.compile(
    r"\b(?:python|java|javascript|typescript|php|c\+\+|c#|c\b|html5?|css3?|sql|postgresql|mysql|sqlite|oracle|mongodb|redis|fastapi|django|flask|spring|react|next\.js|node\.js|docker|kubernetes|git|github|linux|azure|aws|gcp|tensorflow|pytorch|scikit-learn|power\s?bi)\b",
    flags=re.IGNORECASE,
)


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


def _is_llm_output_parsing_failure(exc: Exception) -> bool:
    lowered = str(exc).lower()
    return any(
        token in lowered
        for token in (
            "fallback parsing failed",
            "fallback response is empty",
            "no json object found",
            "json payload is not an object",
            "structured output could not be parsed",
            "json",
        )
    )


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

    attempts = [user_prompt, _truncate_prompt(user_prompt, max_chars=12000)]
    last_error: Exception | None = None
    for attempt_prompt in attempts:
        try:
            response = llm.chat(
                [
                    ChatMessage(role=MessageRole.SYSTEM, content=fallback_system),
                    ChatMessage(role=MessageRole.USER, content=attempt_prompt),
                ]
            )
            content = _extract_response_text(response)
            if not content:
                raise ValueError("Fallback response is empty")
            data = _extract_json_object(content)
            return output_cls.model_validate(data)
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise ValueError(f"Fallback parsing failed: {last_error}") from last_error
    raise ValueError("Fallback response is empty")


def _truncate_prompt(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[TRONQUE POUR RETRY Fallback]"


def _extract_response_text(response: object) -> str | None:
    message = getattr(response, "message", None)
    message_content = getattr(message, "content", None) if message is not None else None
    extracted = _extract_text_payload(message_content)
    if extracted:
        return extracted

    raw = getattr(response, "raw", None)
    raw_text = _extract_text_payload(raw)
    if raw_text:
        return raw_text

    text_attr = getattr(response, "text", None)
    text_value = _extract_text_payload(text_attr)
    if text_value:
        return text_value

    return None


def _extract_text_payload(payload: object) -> str | None:
    if isinstance(payload, str):
        text = payload.strip()
        return text or None

    if isinstance(payload, list):
        parts: list[str] = []
        for item in payload:
            nested = _extract_text_payload(item)
            if nested:
                parts.append(nested)
        if parts:
            return "\n".join(parts)
        return None

    if isinstance(payload, dict):
        if isinstance(payload.get("text"), str) and payload["text"].strip():
            return str(payload["text"]).strip()
        if isinstance(payload.get("content"), str) and payload["content"].strip():
            return str(payload["content"]).strip()

        choices = payload.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                nested = _extract_text_payload(choice)
                if nested:
                    return nested

        message = payload.get("message")
        if message is not None:
            nested = _extract_text_payload(message)
            if nested:
                return nested

        delta = payload.get("delta")
        if delta is not None:
            nested = _extract_text_payload(delta)
            if nested:
                return nested

    return None


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


def _extract_skills_from_cv_markdown(cv_markdown: str) -> list[str]:
    parsed: list[str] = []
    parsed.extend(_extract_skill_section_values(cv_markdown))
    parsed.extend(_extract_known_tech_tokens(cv_markdown))

    deduped: list[str] = []
    seen: set[str] = set()
    for value in parsed:
        normalized = _normalize_skill_label(value)
        token = _normalized_key(normalized)
        if not normalized or not _is_probable_skill(normalized):
            continue
        if token in seen:
            continue
        seen.add(token)
        deduped.append(normalized)
        if len(deduped) >= 20:
            break
    return deduped


def _extract_skill_section_values(cv_markdown: str) -> list[str]:
    lines = cv_markdown.splitlines()
    in_skill_block = False
    values: list[str] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            if in_skill_block:
                in_skill_block = False
            continue

        plain = line.lstrip("#-*").strip()
        lower_key = _normalized_key(plain)

        if lower_key in SKILL_SECTION_KEYS:
            in_skill_block = True
            continue

        if lower_key in SKILL_STOP_TITLES:
            in_skill_block = False
            continue

        if ":" in plain:
            left, right = plain.split(":", maxsplit=1)
            left_key = _normalized_key(left)
            if left_key in SKILL_SECTION_KEYS:
                in_skill_block = True
                values.extend(_split_skill_candidates(right))
                continue
            if in_skill_block and left_key in SKILL_STOP_TITLES:
                in_skill_block = False
                continue

        if in_skill_block:
            values.extend(_split_skill_candidates(plain))

    return values


def _split_skill_candidates(raw: str) -> list[str]:
    parts = re.split(r"[,;|•·/]", raw)
    output: list[str] = []
    for part in parts:
        cleaned = part.strip(" -\t\n\r")
        if cleaned:
            output.append(cleaned)
    return output


def _extract_known_tech_tokens(cv_markdown: str) -> list[str]:
    matches = TECH_TOKEN_PATTERN.findall(cv_markdown)
    return [match.strip() for match in matches if match.strip()]


def _normalize_skill_label(value: str) -> str:
    cleaned = value.strip().strip(".,:;()[]{}")
    compact = re.sub(r"\s+", " ", cleaned)
    mapping = {
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "node.js": "Node.js",
        "next.js": "Next.js",
        "c++": "C++",
        "c#": "C#",
        "html": "HTML",
        "html5": "HTML5",
        "css": "CSS",
        "css3": "CSS3",
        "sql": "SQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "sqlite": "SQLite",
        "mongodb": "MongoDB",
        "power bi": "Power BI",
        "scikit-learn": "Scikit-learn",
        "github": "GitHub",
    }
    lowered = compact.lower()
    if lowered in mapping:
        return mapping[lowered]
    if len(compact) <= 4 and compact.upper() == compact:
        return compact
    return compact


def _is_probable_skill(value: str) -> bool:
    lowered = value.lower()
    token = _normalized_key(value)
    if not token or len(token) < 2:
        return False
    if any(noise in lowered for noise in SKILL_NOISE_TOKENS):
        return False
    if "@" in value:
        return False
    if re.search(r"\d{4}", value):
        return False
    if len(value.split()) > 4:
        return False
    return True


def _merge_skill_lists(primary: list[str], secondary: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for source in (primary, secondary):
        for item in source:
            normalized = _normalize_skill_label(item)
            token = _normalized_key(normalized)
            if not normalized or token in seen or not _is_probable_skill(normalized):
                continue
            seen.add(token)
            merged.append(normalized)
            if len(merged) >= 20:
                return merged
    return merged


def _should_use_heuristic_candidate(candidate: CandidatInfo) -> bool:
    has_contact = bool(candidate.email or candidate.telephone)
    has_skills = len(candidate.skills) >= 4
    return has_contact and has_skills


def _build_candidate_fallback(cv_markdown: str) -> CandidatInfo:
    nom, email, telephone = sanitize_candidate_identity(None, None, None, cv_markdown)
    return CandidatInfo(
        nom=nom,
        email=email,
        telephone=telephone,
        formations=[],
        experiences=[],
        skills=_extract_skills_from_cv_markdown(cv_markdown),
    )


def _extract_fiche_keywords(fiche_de_poste: str) -> list[str]:
    normalized = fiche_de_poste.replace("\n", " ")
    chunks = re.split(r"[,;/|]", normalized)
    keywords: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        value = chunk.strip(" -\t\n\r")
        token = _normalized_key(value)
        if len(token) < 4 or token in seen:
            continue
        seen.add(token)
        keywords.append(value)
        if len(keywords) >= 12:
            break
    return keywords


def _heuristic_score(fiche_de_poste: str, cv_markdown: str) -> int:
    fiche_tokens = {
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ]{4,}", fiche_de_poste.lower())
        if token not in {"avec", "pour", "dans", "des", "les", "une", "par", "sur"}
    }
    cv_tokens = {
        token
        for token in re.findall(r"[a-zA-ZÀ-ÿ]{4,}", cv_markdown.lower())
        if token not in {"avec", "pour", "dans", "des", "les", "une", "par", "sur"}
    }
    if not fiche_tokens:
        return 60
    overlap = len(fiche_tokens.intersection(cv_tokens))
    ratio = overlap / max(1, min(len(fiche_tokens), 40))
    score = int(round(45 + ratio * 45))
    return max(35, min(90, score))


def _build_evaluation_fallback(fiche_de_poste: str, cv_markdown: str) -> EvaluationCv:
    score = _heuristic_score(fiche_de_poste, cv_markdown)
    if score >= 75:
        recommendation = RecommendationValue.A_CONVOQUER
    elif score >= 55:
        recommendation = RecommendationValue.A_ETUDIER
    else:
        recommendation = RecommendationValue.NE_CORRESPOND_PAS

    candidate_skills = _extract_skills_from_cv_markdown(cv_markdown)
    fiche_keywords = _extract_fiche_keywords(fiche_de_poste)

    points_forts: list[str] = []
    if candidate_skills:
        points_forts.append(
            f"Competences explicites detectees: {', '.join(candidate_skills[:3])}")
    points_forts.append("CV lisible avec informations de contact identifiees")
    points_forts.append("Parcours exploitable pour une preselection RH")

    points_manquants: list[str] = []
    if fiche_keywords:
        points_manquants.append(
            f"Verifier en entretien la maitrise de: {', '.join(fiche_keywords[:3])}"
        )
    points_manquants.append("Confirmer le niveau d'autonomie sur les missions cles")
    points_manquants.append(
        "Valider les experiences recentes par des exemples concrets")

    questions = [
        "Pouvez-vous decrire votre realisation la plus pertinente pour ce poste ?",
        (
            "Quelles competences techniques appliquez-vous au quotidien "
            "et dans quel contexte ?"
        ),
        "Quels sont vos objectifs d'evolution sur les 12 prochains mois ?",
    ]

    justification = (
        "Analyse produite en mode de secours car la reponse structuree IA "
        "etait invalide. Une preselection automatique a ete calculee "
        "a partir du contenu du CV et de la fiche de poste."
    )

    return EvaluationCv(
        score_matching=score,
        points_forts=points_forts[:5],
        points_manquants=points_manquants[:5],
        recommandation=recommendation,
        justification_ia=justification,
        questions_entretien=questions,
    )


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
    heuristic_skills = _extract_skills_from_cv_markdown(cv_markdown)
    candidate.skills = _merge_skill_lists(candidate.skills, heuristic_skills)
    return candidate


def extract_candidat_info(cv_markdown: str) -> CandidatInfo:
    """Agent 1 - Extract candidate information from CV markdown."""
    heuristic_candidate = _build_candidate_fallback(cv_markdown)
    if _should_use_heuristic_candidate(heuristic_candidate):
        return _post_validate_candidate(heuristic_candidate, cv_markdown)

    user_prompt = (
        f"CV (Markdown brut, conserve tel quel):\n```markdown\n{cv_markdown}\n```"
    )
    try:
        candidate = _run_structured_chat(
            CandidatInfo, EXTRACTION_SYSTEM_PROMPT, user_prompt
        )
    except Exception as exc:
        if not _is_llm_output_parsing_failure(exc):
            raise
        candidate = heuristic_candidate

    candidate.skills = _merge_skill_lists(candidate.skills, heuristic_candidate.skills)
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
    try:
        return _run_structured_chat(EvaluationCv, EVALUATION_SYSTEM_PROMPT, user_prompt)
    except Exception as exc:
        if not _is_llm_output_parsing_failure(exc):
            raise
        return _build_evaluation_fallback(fiche_de_poste, cv_markdown)
