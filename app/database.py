
# Importe les outils SQLAlchemy pour se connecter à SQLite.
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Définit le chemin de la base de données SQLite.
DATABASE_URL = "sqlite:///./salesbot.db"

# Crée le moteur de connexion à la base de données.
# check_same_thread=False est nécessaire pour cet usage avec FastAPI.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Prépare la création de sessions utilisées pour lire et modifier les données.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base commune aux modèles SQLAlchemy.
Base = declarative_base()


def get_db():
    """Fournit une session de base de données à une route API."""

    # Ouvre une nouvelle session.
    db = SessionLocal()

    try:
        # Transmet la session à la route qui en a besoin.
        yield db
    finally:
        # Ferme toujours la session après utilisation.
        db.close()
