
from pydantic import BaseModel, ConfigDict


class LeadResponse(BaseModel):
    """
    Définit la structure publique d'un prospect renvoyé par l'API.

    Ce modèle permet à FastAPI de vérifier et documenter
    les données retournées au client.
    """

    # Identifiant unique généré par la base de données.
    id: int

    # Nom du prospect.
    name: str

    # Adresse e-mail du prospect.
    email: str

    # Entreprise facultative.
    company: str | None = None

    # Autorise Pydantic à lire les attributs d'un objet SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)
