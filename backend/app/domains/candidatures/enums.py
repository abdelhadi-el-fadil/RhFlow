"""Candidatures domain enums."""

from enum import Enum


class CandidatureStatut(str, Enum):
    RECU = "RECU"
    EN_COURS = "EN_COURS"
    EVALUE = "EVALUE"
    ERREUR = "ERREUR"
    RETENU = "RETENU"
    REJETE = "REJETE"


class RecommandationIA(str, Enum):
    A_CONVOQUER = "A_CONVOQUER"
    A_ETUDIER = "A_ETUDIER"
    NE_CORRESPOND_PAS = "NE_CORRESPOND_PAS"
