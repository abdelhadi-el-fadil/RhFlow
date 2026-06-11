"""
Service — domaine "auth".

Contient toute la logique métier de l'authentification : vérification des
identifiants, émission et validation des JWT. Le router ne fait que router
les requêtes HTTP vers ces fonctions et empaqueter le résultat.
"""
from sqlalchemy.orm import Session

from app.core.security import (
    ExpiredSignatureError,
    InvalidTokenError,
    create_access_token,
    decode_token,
    verify_password,
)
from app.domains.auth.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
)
from app.domains.auth.schemas import TokenResponse
from app.domains.users.exceptions import UserNotFoundException
from app.domains.users.model import User


def login(db: Session, email: str, password: str) -> TokenResponse:
    """
    Vérifie les identifiants et retourne un JWT.

    Le même message d'erreur est utilisé que l'email soit inconnu ou que le
    mot de passe soit faux (anti-énumération des comptes).
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException()

    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
    )
    return TokenResponse(access_token=token)


def get_current_user_from_token(db: Session, token: str) -> User:
    """
    Décode le JWT, valide son contenu, et retourne l'utilisateur correspondant.
    """
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise TokenExpiredException()
    except InvalidTokenError:
        raise InvalidTokenException()

    user_id = payload.get("sub")
    if user_id is None:
        raise InvalidTokenException()

    user = db.get(User, int(user_id))
    if user is None:
        raise UserNotFoundException()

    return user