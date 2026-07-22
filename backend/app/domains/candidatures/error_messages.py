"""Helpers to convert candidature processing errors into readable messages."""

from __future__ import annotations


def humanize_candidature_error(detail: str | None) -> str | None:
    if detail is None:
        return None

    normalized = detail.strip()
    if not normalized:
        return None

    lowered = normalized.lower()

    if "parsed cv markdown is empty" in lowered:
        return (
            "Le CV a ete recu, mais aucun texte exploitable n'a pu etre extrait. "
            "Verifiez que le fichier est lisible et contient bien du texte."
        )

    if "duplicate candidate email" in lowered:
        return (
            "Une candidature avec la meme adresse email existe deja dans ce projet. "
            "Supprimez le doublon ou utilisez un autre CV."
        )

    if "retry budget" in lowered or "exhausted retry budget" in lowered:
        return (
            "Le service IA n'a pas reussi a produire une reponse valide dans "
            "le temps imparti. "
            "Relancez l'analyse; si le probleme persiste, verifiez la latence "
            "ou la disponibilite du fournisseur IA."
        )

    if "timeout" in lowered or "timed out" in lowered:
        return (
            "Le traitement a depasse le temps autorise. "
            "Relancez l'analyse ou verifiez la disponibilite des services IA."
        )

    if "429" in lowered or "too many requests" in lowered or "rate limit" in lowered:
        return (
            "Le service IA est temporairement surcharge. "
            "Relancez le traitement dans quelques instants."
        )

    if "storage" in lowered or "minio" in lowered:
        return (
            "Le fichier du CV n'a pas pu etre lu depuis le stockage. "
            "Verifiez le service de stockage et reessayez."
        )

    if "json" in lowered or "decode" in lowered:
        return (
            "Le service d'analyse a renvoye une reponse invalide. "
            "Relancez le traitement ou verifiez la configuration IA."
        )

    if (
        "structured output could not be parsed" in lowered
        or "fallback parsing failed" in lowered
        or "llm evaluation missing score_matching" in lowered
        or "llm evaluation missing valid recommandation" in lowered
        or "llm evaluation missing justification_ia" in lowered
    ):
        return (
            "Le modele IA a renvoye une sortie incomplete ou non conforme au "
            "format attendu. "
            "Relancez l'analyse ou ajustez les consignes du modele."
        )

    if "forbidden" in lowered or "403" in lowered:
        return (
            "Le traitement n'a pas les autorisations necessaires pour acceder"
            " a cette candidature."
        )

    return (
        "Le traitement automatique a echoue. Consultez le detail technique ci-dessous "
        "pour identifier la cause exacte."
    )