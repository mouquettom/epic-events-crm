from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest

from app.models.employee import Role
from app.session.current_session import CurrentSession
from app.utils import jwt as jwt_utils
from app.utils.exceptions import AuthorizationError, SessionExpiredError
from app.utils.jwt import create_access_token


def make_employee(employee_id: int = 1):
    return SimpleNamespace(id=employee_id, role=Role.GESTION)


def make_token(employee_id: int, expires_in: timedelta) -> str:
    """Crée un jeton signé avec la clé de l'application."""

    now = datetime.now(UTC)

    return jwt.encode(
        {
            "sub": str(employee_id),
            "iat": now - timedelta(hours=2),
            "exp": now + expires_in,
        },
        jwt_utils.JWT_SECRET_KEY,
        algorithm=jwt_utils.JWT_ALGORITHM,
    )


def logged_in_session(token: str, employee_id: int = 1) -> CurrentSession:
    session = CurrentSession()
    session.login(employee=make_employee(employee_id), access_token=token)
    return session


def test_login_and_logout() -> None:
    session = logged_in_session("token")

    assert session.is_authenticated is True
    assert session.access_token == "token"

    session.logout()

    assert session.is_authenticated is False
    assert session.current_employee is None
    assert session.access_token is None


def test_valid_token_keeps_the_session_open() -> None:
    session = logged_in_session(create_access_token(1))

    session.ensure_token_is_valid()

    assert session.is_authenticated is True


def test_expired_token_closes_the_session() -> None:
    session = logged_in_session(make_token(1, timedelta(seconds=-1)))

    with pytest.raises(
        SessionExpiredError,
        match="Votre session a expiré. Veuillez vous reconnecter.",
    ):
        session.ensure_token_is_valid()

    assert session.is_authenticated is False
    assert session.access_token is None


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        jwt.encode(
            {"sub": "1", "exp": datetime.now(UTC) + timedelta(hours=1)},
            "another-secret-key-that-is-long-enough-for-hs256",
            algorithm="HS256",
        ),
    ],
)
def test_invalid_token_closes_the_session(token: str) -> None:
    session = logged_in_session(token)

    with pytest.raises(
        SessionExpiredError,
        match="Votre session n'est plus valide",
    ):
        session.ensure_token_is_valid()

    assert session.is_authenticated is False


def test_token_of_another_employee_closes_the_session() -> None:
    session = logged_in_session(create_access_token(2), employee_id=1)

    with pytest.raises(
        SessionExpiredError,
        match="Votre session n'est plus valide",
    ):
        session.ensure_token_is_valid()

    assert session.is_authenticated is False


def test_check_without_session_raises() -> None:
    with pytest.raises(SessionExpiredError, match="Aucune session active"):
        CurrentSession().ensure_token_is_valid()


def test_session_expired_error_is_an_authorization_error() -> None:
    assert issubclass(SessionExpiredError, AuthorizationError)
