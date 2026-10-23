"""Cas limites qui provoquaient une erreur technique avec une vraie base."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.employee import Role
from app.services.contract_service import ContractService
from app.services.employee_service import EmployeeService
from app.services.event_service import EventService
from app.utils.exceptions import ValidationError
from tests.factories import (
    create_client,
    create_contract,
    create_employee,
    create_event,
)


def test_support_can_change_only_the_start_date(db_session: Session) -> None:
    commercial = create_employee(db_session, role=Role.COMMERCIAL)
    support = create_employee(db_session, role=Role.SUPPORT)
    client = create_client(db_session, commercial=commercial)
    contract = create_contract(db_session, client=client, commercial=commercial)
    event = create_event(db_session, contract=contract, support=support)

    # Saisie console : format JJ/MM/AAAA HH:MM, donc une date sans fuseau.
    new_start = datetime.combine(
        event.start_date.date(),
        datetime.min.time(),
    ) + timedelta(hours=1)

    updated_event = EventService(db_session).update_event(
        current_employee=support,
        event_id=event.id,
        start_date=new_start,
    )

    assert updated_event.start_date < updated_event.end_date


@pytest.mark.parametrize("amount", ["nan", "inf", "100000000"])
def test_create_contract_rejects_unstorable_amounts(
    db_session: Session,
    amount: str,
) -> None:
    management = create_employee(db_session, role=Role.GESTION)
    commercial = create_employee(db_session, role=Role.COMMERCIAL)
    client = create_client(db_session, commercial=commercial)

    with pytest.raises(ValidationError):
        ContractService(db_session).create_contract(
            current_employee=management,
            client_id=client.id,
            total_amount=Decimal(amount),
            remaining_amount=Decimal("0"),
        )


def test_delete_commercial_with_clients_is_refused(db_session: Session) -> None:
    management = create_employee(db_session, role=Role.GESTION)
    commercial = create_employee(db_session, role=Role.COMMERCIAL)
    client = create_client(db_session, commercial=commercial)

    with pytest.raises(
        ValidationError,
        match="encore responsable de clients ou de contrats",
    ):
        EmployeeService(db_session).delete_employee(
            current_employee=management,
            employee_id=commercial.id,
        )

    db_session.refresh(client)
    assert client.commercial_id == commercial.id


def test_delete_support_unassigns_their_events(db_session: Session) -> None:
    management = create_employee(db_session, role=Role.GESTION)
    commercial = create_employee(db_session, role=Role.COMMERCIAL)
    support = create_employee(db_session, role=Role.SUPPORT)
    client = create_client(db_session, commercial=commercial)
    contract = create_contract(db_session, client=client, commercial=commercial)
    event = create_event(db_session, contract=contract, support=support)

    EmployeeService(db_session).delete_employee(
        current_employee=management,
        employee_id=support.id,
    )

    db_session.refresh(event)
    assert event.support_id is None
