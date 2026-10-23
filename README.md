# Epic Events CRM

[![CI](https://github.com/mouquettom/epic-events-crm/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mouquettom/epic-events-crm/actions/workflows/ci.yml)

Command-line CRM application developed in Python to manage employees, clients, contracts, and events for the fictional company **Epic Events**.

The project uses a layered architecture to clearly separate the user interface, business rules, and data access.

---

## Features

### Authentication

- Login with email and password
- Password hashing with bcrypt
- JWT token generation
- User session management
- Access token expiration
- Secure logout

### Employee Management

Features restricted to the management department:

- List employees
- View an employee
- Create an employee
- Update an employee
- Delete an employee
- Prevent users from deleting their own account
- Prevent the deletion of a sales employee who still owns clients or contracts
- Assign `GESTION`, `COMMERCIAL`, and `SUPPORT` roles

### Client Management

- Client creation by a sales employee
- Automatic assignment of the client to the logged-in sales employee
- Duplicate email detection
- Read-only access to all clients for every role
- Updates restricted to the sales employee in charge of the client

### Contract Management

- Contract creation by the management department, linked to the client's sales employee
- Manage total and remaining amounts (up to 99,999,999.99)
- Sign a contract
- Read-only access to all contracts for every role
- Updates by the management department or by the sales employee in charge of the contract
- List of a sales employee's unsigned contracts
- List of a sales employee's contracts with an outstanding balance

### Event Management

- Event creation by the sales employee in charge of a signed contract
- Manage dates, location, number of attendees, and notes
- Read-only access to all events for every role
- Assignment (or reassignment) of a support employee by the management department
- List of events without assigned support
- List of the events assigned to the logged-in support employee
- Updates restricted to the support employee assigned to the event

### Monitoring

- Technical error reporting with Sentry
- Distinction between business errors and unexpected errors
- Configurable Sentry environment
- No personal data sent by default

---

## Roles and Permissions

### GESTION

The management department can:

- create, view, update, and delete employees;
- view all clients;
- create, view, and update all contracts;
- view all events;
- list events without assigned support;
- assign a support employee to an event.

### COMMERCIAL

A sales employee can:

- create clients, which are automatically assigned to them;
- view all clients and update their own clients;
- view all contracts and update the contracts of their own clients;
- list their unsigned contracts and their contracts with an outstanding balance;
- create an event for a signed contract of one of their clients;
- view all events.

### SUPPORT

A support employee can:

- view all clients;
- view all contracts;
- view all events and list the events assigned to them;
- update the events assigned to them.

No role can delete clients, contracts, or events from the application.

Permissions are enforced in the `services` layer, independently of the menus displayed in the interface.

---

## Architecture

```
OC_P12_EpicEvents/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── app/
│   ├── controllers/
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── session/
│   └── utils/
│
├── migrations/
├── tests/
│   ├── functional/
│   ├── integration/
│   ├── unit/
│   ├── conftest.py
│   ├── factories.py
│   └── README.md
│
├── .env.example
├── .flake8
├── .gitignore
├── alembic.ini
├── main.py
├── pytest.ini
├── requirements.txt
└── README.md

```

### Layer Organization

```
CLI Interface
    ↓
Controllers
    ↓
Services
    ↓
Repositories
    ↓
SQLAlchemy
    ↓
PostgreSQL

```

- **Controllers** handle console input and output.
- **Services** enforce business rules and permissions.
- **Repositories** perform SQLAlchemy queries.
- **Models** define database tables and their relationships.
- `CurrentSession` stores the employee and token for the active session.
- Utilities handle exceptions, passwords, JWTs, and Sentry.

---

## Technologies Used

- Python 3
- PostgreSQL
- SQLAlchemy 2
- Alembic
- psycopg
- PyJWT
- bcrypt
- python-dotenv
- Sentry SDK
- pytest
- pytest-cov
- Flake8
- Black
- GitHub Actions

---

## Prerequisites

- Python 3.11 or later
- PostgreSQL
- Git
- A Python virtual environment
- An optional Sentry project for error monitoring

---

## Installation

### 1. Clone the Repository

```
git clone https://github.com/mouquettom/epic-events-crm.git
cd epic-events-crm
```

### 2. Create a Virtual Environment

On macOS or Linux:

```
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

---

## Environment Configuration

Copy the example file:

```
cp .env.example .env
```

Then set the variables in `.env`:

```
DB_USER=epic_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=epic_events

TEST_DB_USER=epic_user
TEST_DB_PASSWORD=your_database_password
TEST_DB_HOST=localhost
TEST_DB_PORT=5432
TEST_DB_NAME=epic_events_test

JWT_SECRET_KEY=replace_with_a_long_random_secret

SENTRY_DSN=
SENTRY_ENVIRONMENT=development
```

The `TEST_DB_*` variables point to a dedicated database used by the test suite (see [Test Database](#test-database)).

The `.env` file contains sensitive information and must never be committed to version control.

### Generate a JWT Secret Key

```
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Configure Sentry

After creating a Python project in Sentry, retrieve the DSN from:

```
Settings → Projects → Client Keys (DSN)

```

Then add it to `.env`:

```
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
SENTRY_ENVIRONMENT=development
```

The application also works without Sentry if `SENTRY_DSN` is left empty.

---

## PostgreSQL Configuration

PostgreSQL must be installed and the server must be running before proceeding.

### Connect to PostgreSQL

From a terminal, connect using a PostgreSQL user with sufficient privileges to create a database and a user.

For example:

```
psql -d postgres
```

Depending on your local configuration, you may need to specify the user:

```
psql -U postgres -d postgres
```

### Create the Database and User

From the PostgreSQL prompt:

```
CREATE DATABASE epic_events;

CREATE USER epic_user
WITH PASSWORD 'your_database_password';

GRANT ALL PRIVILEGES
ON DATABASE epic_events
TO epic_user;
```

The password must match the `DB_PASSWORD` value defined in the `.env` file.

### Grant Schema Permissions

Connect to the newly created database:

```
\c epic_events
```

Then allow `epic_user` to use and create objects in the `public` schema:

```
GRANT USAGE, CREATE
ON SCHEMA public
TO epic_user;
```

Exit PostgreSQL:

```
\q

```

The database is now ready for Alembic migrations.

### Test Database

The test suite uses its own database so that it never touches application data. Functional tests empty its tables before and after each scenario.

From the PostgreSQL prompt:

```
CREATE DATABASE epic_events_test OWNER epic_user;
```

The tables are created automatically by `tests/conftest.py` when the tests start.

---

## Alembic Migrations

Alembic is the recommended method for creating and updating the database schema.

Apply all migrations:

```
alembic upgrade head
```

Display the current migration:

```
alembic current
```

Display the migration history:

```
alembic history
```

Create a new migration after modifying the models:

```
alembic revision --autogenerate -m "Migration description"
```

Then apply it:

```
alembic upgrade head
```

The `app/database/init_db.py` script may be used in some development contexts, but Alembic should remain the source of truth for the project schema.

---

## Creating the First Management Account

Once the database and tables are ready:

```
python -m app.database.create_admin
```

The created account is automatically assigned the `GESTION` role.

---

## Running the Application

```
python main.py
```

After login, the displayed menu depends on the employee's role.

---

## Security

### Passwords

Passwords are hashed with bcrypt and are never stored in plain text.

The current password policy requires at least eight characters.

### JWT

JWT tokens:

- are signed using `HS256`;
- contain the employee ID;
- expire after sixty minutes;
- use a secret key loaded from the `.env` file.

### Sensitive Variables

The following items must never be committed to the Git repository:

- `.env`
- PostgreSQL passwords
- JWT secret key
- JWT tokens
- integration secrets
- real personal information

---

## Sentry

Sentry is initialized at application startup when `SENTRY_DSN` is defined.

Business exceptions such as:

- `ValidationError`
- `AuthorizationError`
- `DuplicateError`
- `NotFoundError`

are displayed to the user without being treated as technical errors.

Unexpected exceptions are sent to Sentry from `main.py`.

The configuration disables the automatic transmission of personal data:

```
send_default_pii=False
```

---

## Tests

Tests are divided into three categories.

### Unit Tests

```
pytest tests/unit -v
```

### Integration Tests

```
pytest tests/integration -v
```

### Functional Tests

```
pytest tests/functional -v
```

### Run the Full Test Suite

```
pytest
```

At the time of the project's latest validation:

```
486 tests passed
92% coverage of the app package

```

These values may change as the codebase evolves. The CI job page always shows the current figures.

### Coverage

```
pytest --cov=app --cov-report=term-missing
```

Generate an HTML report:

```
pytest --cov=app --cov-report=html
```

The report is then available at:

```
htmlcov/index.html

```

---

## Continuous Integration

Every push to `main` and every pull request triggers the GitHub Actions workflow defined in `.github/workflows/ci.yml`. The badge at the top of this README shows the status of the latest run on `main`.

A `Lint` job runs Flake8 with the project's `.flake8` configuration.

For each supported Python version (3.11, 3.12 and 3.13), the `Tests` job:

1. starts a PostgreSQL 16 service container;
2. installs the dependencies from `requirements.txt`;
3. creates the test database `epic_events_test`;
4. applies the Alembic migrations with `alembic upgrade head`;
5. runs `alembic check` to make sure the models and the migrations are in sync;
6. rolls every migration back with `alembic downgrade base`, then reapplies them;
7. runs the full test suite with coverage and fails if coverage of the `app` package drops below 90%.

The coverage table is added to the summary of the Python 3.13 job, and the HTML and XML reports are available as the `coverage-report` artifact of each run.

The database credentials and the JWT key used by the workflow are throwaway values that only exist inside the CI environment. No repository secret is required.

The workflow can also be started manually from the **Actions** tab (**Run workflow**).

---

## Code Quality

### Black

Black is not part of `requirements.txt` and is not checked by the CI yet: applying it would reformat most files. Install it with `pip install black` if needed.

Check formatting:

```
black --check app tests main.py
```

Apply formatting:

```
black app tests main.py
```

### Flake8

The configuration lives in `.flake8` (88-character lines, migrations excluded). The CI runs the same command:

```
flake8 app tests main.py
```

---

## Main Business Rules

- Only a management employee can manage employees.
- An employee cannot delete their own account.
- A sales employee who still owns clients or contracts cannot be deleted.
- Deleting a support employee unassigns the events they were in charge of.
- Only a sales employee can create a client.
- A sales employee can only update their own clients.
- Only the management department can create a contract.
- A contract is automatically linked to the sales employee in charge of its client.
- Amounts must be valid numbers and cannot exceed 99,999,999.99.
- The total amount must be positive; the remaining amount cannot be negative or exceed the total amount.
- An event can only be created by the sales employee in charge of a signed contract.
- An event's end date must be after its start date, and the number of attendees must be positive.
- Only the management department can assign a support employee.
- A support employee can only update events assigned to them.
- Unexpected technical errors are reported to Sentry.

---

## Possible Improvements

- Allow reassigning clients to another sales employee (required before deleting a sales employee who owns clients)
- Filter a sales employee's client list by ownership
- Complete field validation when updating an employee
- Add a password reset command
- Centralize environment variable configuration
- Add a web interface or REST API
- Apply Black formatting to the codebase and check it in the continuous integration workflow

---

## Author

@tom_mouquet

Project developed as part of the OpenClassrooms **Développeur
d'application Python** training program.
