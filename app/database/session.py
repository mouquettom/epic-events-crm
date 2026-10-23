import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker


load_dotenv()

REQUIRED_VARIABLES = ("DB_USER", "DB_HOST", "DB_PORT", "DB_NAME")

missing_variables = [
    name for name in REQUIRED_VARIABLES if not os.getenv(name)
]

if missing_variables:
    raise RuntimeError(
        "Variables de connexion PostgreSQL absentes du fichier .env : "
        + ", ".join(missing_variables)
    )

# URL.create échappe les caractères spéciaux (@, :, /, %...)
# qu'un mot de passe peut contenir.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.getenv("DB_PASSWORD") or None,
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
