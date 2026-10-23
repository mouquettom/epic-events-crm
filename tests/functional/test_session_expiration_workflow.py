import jwt
from sqlalchemy.orm import Session, sessionmaker

from app.models.employee import Role
from main import run_application
from tests.functional.helpers import seed_employee


def test_expired_session_returns_to_the_login_screen(
    monkeypatch,
    capsys,
    functional_session_factory: sessionmaker[Session],
) -> None:
    support = seed_employee(
        functional_session_factory,
        first_name="Sam",
        last_name="Support",
        email="support@functional.test",
        password="SupportPassword123!",
        role=Role.SUPPORT,
    )

    user_inputs = iter(
        [
            "1",  # se connecter
            support.email,
            "3",  # consulter et suivre les événements
            "0",  # quitter depuis l'écran de connexion
        ]
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _message="": next(user_inputs),
    )
    monkeypatch.setattr(
        "app.controllers.auth_controller.getpass",
        lambda _message="": "SupportPassword123!",
    )

    # La connexion se passe normalement, puis le jeton expire avant
    # la première action (comme après 60 minutes d'inactivité).
    def expired_token(_token: str) -> int:
        raise jwt.ExpiredSignatureError("Signature has expired")

    monkeypatch.setattr(
        "app.session.current_session.decode_access_token",
        expired_token,
    )

    run_application(session_factory=functional_session_factory)

    output = capsys.readouterr().out

    assert "Connexion réussie" in output
    assert "Votre session a expiré. Veuillez vous reconnecter." in output
    assert "Suivi des événements" not in output
    assert "erreur technique" not in output
    assert "Fermeture de l'application." in output
