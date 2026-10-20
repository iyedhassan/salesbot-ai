
from sqlalchemy import Column, Integer, String
from app.database import Base


class LeadDB(Base):
    """
    Modèle SQLAlchemy représentant les prospects dans SQLite.
    """

    # Nom de la table dans la base de données.
    __tablename__ = "leads"

    # Identifiant unique généré automatiquement.
    id = Column(Integer, primary_key=True, index=True)

    # Nom obligatoire du prospect.
    name = Column(String, nullable=False)

    # Adresse e-mail obligatoire et unique.
    # unique=True demande à SQLite d'interdire les doublons.
    email = Column(String, nullable=False, unique=True, index=True)

    # Nom de l'entreprise, facultatif.
    company = Column(String, nullable=True)
