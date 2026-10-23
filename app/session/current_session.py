import logging

import jwt

from app.models.employee import Employee
from app.utils.exceptions import SessionExpiredError
from app.utils.jwt import decode_access_token


logger = logging.getLogger(__name__)


class CurrentSession:
    """ Mémorise l'employé actuellement connecté à l'application. """

    def __init__(self) -> None:
        self._current_employee: Employee | None = None
        self._access_token: str | None = None

    @property
    def current_employee(self) -> Employee | None:
        return self._current_employee

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def is_authenticated(self) -> bool:
        return self._current_employee is not None

    def login(
        self,
        employee: Employee,
        access_token: str,
    ) -> None:
        self._current_employee = employee
        self._access_token = access_token

    def logout(self) -> None:
        self._current_employee = None
        self._access_token = None

    def ensure_token_is_valid(self) -> None:
        """
        Revérifie le jeton de la session avant une action.

        Si le jeton a expiré, n'est plus valide ou ne correspond pas
        au collaborateur connecté, la session est fermée et
        SessionExpiredError est levée.
        """

        employee = self._current_employee

        if employee is None or self._access_token is None:
            raise SessionExpiredError(
                "Aucune session active. Veuillez vous reconnecter."
            )

        try:
            employee_id = decode_access_token(self._access_token)

        except jwt.ExpiredSignatureError as error:
            self._close_expired_session(employee.id, "jeton expiré")

            raise SessionExpiredError(
                "Votre session a expiré. Veuillez vous reconnecter."
            ) from error

        except jwt.PyJWTError as error:
            self._close_expired_session(employee.id, "jeton invalide")

            raise SessionExpiredError(
                "Votre session n'est plus valide. Veuillez vous reconnecter."
            ) from error

        if employee_id != employee.id:
            self._close_expired_session(
                employee.id,
                "jeton émis pour un autre collaborateur",
            )

            raise SessionExpiredError(
                "Votre session n'est plus valide. Veuillez vous reconnecter."
            )

    def _close_expired_session(
        self,
        employee_id: int,
        reason: str,
    ) -> None:
        logger.info(
            "Session fermée automatiquement (%s) : employee_id=%s.",
            reason,
            employee_id,
        )

        self.logout()
