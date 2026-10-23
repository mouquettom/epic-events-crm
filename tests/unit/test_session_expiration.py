"""Un jeton expiré ferme la session avant toute action."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import jwt
import pytest

from app.controllers.client_controller import ClientController
from app.controllers.contract_controller import ContractController
from app.controllers.employee_controller import EmployeeController
from app.controllers.event_controller import EventController
from app.controllers.main_menu_controller import MainMenuController
from app.models.employee import Employee, Role
from app.session.current_session import CurrentSession
from app.utils import jwt as jwt_utils
from app.utils.exceptions import SessionExpiredError


def expired_session(role: Role) -> CurrentSession:
    employee = Mock(spec=Employee)
    employee.id = 1
    employee.first_name = "Alice"
    employee.last_name = "Martin"
    employee.role = role

    now = datetime.now(UTC)
    expired_token = jwt.encode(
        {
            "sub": "1",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(minutes=1),
        },
        jwt_utils.JWT_SECRET_KEY,
        algorithm=jwt_utils.JWT_ALGORITHM,
    )

    session = CurrentSession()
    session.login(employee=employee, access_token=expired_token)

    return session


@pytest.mark.parametrize(
    ("controller_class", "service_argument", "role", "action"),
    [
        (ClientController, "client_service", Role.COMMERCIAL, "list_clients"),
        (ContractController, "contract_service", Role.GESTION, "list_contracts"),
        (EmployeeController, "employee_service", Role.GESTION, "list_employees"),
        (EventController, "event_service", Role.SUPPORT, "list_events"),
    ],
)
def test_controllers_refuse_actions_once_the_token_has_expired(
    monkeypatch,
    controller_class,
    service_argument,
    role,
    action,
) -> None:
    session = expired_session(role)
    service = Mock()
    controller = controller_class(
        **{service_argument: service},
        current_session=session,
    )
    monkeypatch.setattr(
        "builtins.input",
        Mock(side_effect=AssertionError("aucune saisie attendue")),
    )

    with pytest.raises(SessionExpiredError, match="Votre session a expiré"):
        getattr(controller, action)()

    assert session.is_authenticated is False
    assert service.method_calls == []


def test_main_menu_returns_to_login_when_the_session_expires(
    monkeypatch,
    capsys,
) -> None:
    session = expired_session(Role.GESTION)
    client_controller = ClientController(
        client_service=Mock(),
        current_session=session,
    )
    controller = MainMenuController(
        current_session=session,
        auth_controller=Mock(),
        employee_controller=Mock(),
        client_controller=client_controller,
        contract_controller=Mock(),
        event_controller=Mock(),
    )
    choices = iter(["2"])  # Consulter les clients
    monkeypatch.setattr("builtins.input", lambda _message="": next(choices))

    controller.run()

    output = capsys.readouterr().out
    assert "Votre session a expiré. Veuillez vous reconnecter." in output
    assert session.is_authenticated is False
