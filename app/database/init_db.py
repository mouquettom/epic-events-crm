from app.database.session import engine
from app.models.base import Base

# Importé pour enregistrer tous les modèles SQLAlchemy.
from app import models  # noqa: F401


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    init_db()
    print("Tables créées avec succès.")
