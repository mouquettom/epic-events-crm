import importlib

import dotenv
import pytest

import app.database.session as session_module


DB_VARIABLES = {
    "DB_USER": "epic_user",
    "DB_PASSWORD": "p@ss:w/rd%42",
    "DB_HOST": "db.example.test",
    "DB_PORT": "6543",
    "DB_NAME": "epic_events",
}


@pytest.fixture
def reload_session(monkeypatch):
    """Recharge le module avec un environnement contrôlé, puis le restaure."""

    # Le fichier .env local ne doit pas compléter l'environnement du test.
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)

    def _reload(**variables):
        for name in DB_VARIABLES:
            monkeypatch.delenv(name, raising=False)

        for name, value in variables.items():
            monkeypatch.setenv(name, value)

        return importlib.reload(session_module)

    yield _reload

    monkeypatch.undo()
    importlib.reload(session_module)


def test_database_url_escapes_special_characters(reload_session) -> None:
    module = reload_session(**DB_VARIABLES)

    url = module.DATABASE_URL

    assert url.password == "p@ss:w/rd%42"
    assert url.host == "db.example.test"
    assert url.port == 6543
    assert url.database == "epic_events"
    assert module.engine.url.password == "p@ss:w/rd%42"


def test_password_is_optional(reload_session) -> None:
    variables = {
        name: value
        for name, value in DB_VARIABLES.items()
        if name != "DB_PASSWORD"
    }

    module = reload_session(**variables)

    assert module.DATABASE_URL.password is None


def test_missing_variables_raise_a_clear_error(reload_session) -> None:
    with pytest.raises(RuntimeError, match="DB_HOST, DB_NAME"):
        reload_session(
            DB_USER="epic_user",
            DB_PORT="5432",
        )
