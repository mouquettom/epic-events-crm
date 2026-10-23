"""Opérations CRUD des repositories non couvertes par les autres tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.contract import Contract
from app.models.employee import Role
from app.models.event import Event
from app.repositories.client_repository import ClientRepository
from app.repositories.contract_repository import ContractRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.event_repository import EventRepository
from tests.factories import (
    create_client,
    create_contract,
    create_employee,
    create_event,
)


def test_client_repository_crud(db_session: Session) -> None:
    commercial = create_employee(db_session, role=Role.COMMERCIAL)
    other_commercial = create_employee(db_session, role=Role.COMMERCIAL)
    other_client = create_client(db_session, commercial=other_commercial)
    repository = ClientRepository(db_session)

    client = repository.create(
        Client(
            full_name="Jean Dupont",
            email="jean.dupont@crud.test",
            phone="0601020304",
            company="Dupont SA",
            commercial_id=commercial.id,
        )
    )

    assert client.id is not None
    assert repository.get_by_commercial_id(commercial.id) == [client]
    assert {client, other_client} <= set(repository.get_all())

    client.company = "Dupont & Fils"
    updated_client = repository.update(client)

    assert updated_client.company == "Dupont & Fils"

    repository.delete(client)

    assert repository.get_by_id(client.id) is None


def test_contract_repository_crud(db_session: Session) -> None:
    commercial = create_employee(db_session, role=Role.COMMERCIAL)
    client = create_client(db_session, commercial=commercial)
    other_client = create_client(db_session, commercial=commercial)
    other_contract = create_contract(
        db_session,
        client=other_client,
        commercial=commercial,
    )
    repository = ContractRepository(db_session)

    contract = repository.create(
        Contract(
            total_amount=Decimal("5000.00"),
            remaining_amount=Decimal("5000.00"),
            is_signed=False,
            client_id=client.id,
            commercial_id=commercial.id,
        )
    )

    assert contract.id is not None
    assert repository.get_by_client_id(client.id) == [contract]
    assert repository.get_by_commercial_id(commercial.id) == [
        other_contract,
        contract,
    ]
    assert {contract, other_contract} <= set(repository.get_all())

    contract.remaining_amount = Decimal("1000.00")
    contract.is_signed = True
    updated_contract = repository.update(contract)

    assert updated_contract.remaining_amount == Decimal("1000.00")
    assert updated_contract.is_signed is True

    repository.delete(contract)

    assert repository.get_by_id(contract.id) is None


def test_employee_repository_update(db_session: Session) -> None:
    employee = create_employee(db_session, role=Role.SUPPORT)
    repository = EmployeeRepository(db_session)

    employee.role = Role.GESTION
    updated_employee = repository.update(employee)

    assert updated_employee.role == Role.GESTION


def test_event_repository_crud(db_session: Session) -> None:
    commercial = create_employee(db_session, role=Role.COMMERCIAL)
    client = create_client(db_session, commercial=commercial)
    contract = create_contract(db_session, client=client, commercial=commercial)
    other_event = create_event(db_session, contract=contract)
    repository = EventRepository(db_session)
    start_date = datetime.now(UTC) + timedelta(days=30)

    event = repository.create(
        Event(
            start_date=start_date,
            end_date=start_date + timedelta(hours=3),
            location="Lyon",
            attendees=50,
            notes="Séminaire",
            contract_id=contract.id,
        )
    )

    assert event.id is not None
    assert repository.get_by_contract_id(contract.id) == [other_event, event]
    assert {event, other_event} <= set(repository.get_all())

    event.attendees = 75
    updated_event = repository.update(event)

    assert updated_event.attendees == 75

    repository.delete(event)

    assert repository.get_by_id(event.id) is None
