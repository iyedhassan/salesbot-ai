
from pydantic import BaseModel, ConfigDict
# Importe le modèle de réponse du prospect.
from app.models.lead_response import LeadResponse
class LeadOperationResponse(BaseModel):
    """
    Structure de réponse pour une opération sur un prospect,
    par exemple sa création ou sa mise à jour.
    """

    # Message qui décrit le résultat de l'opération.
    message: str

    # Données du prospect concerné.
    lead: "LeadResponse"

    # Autorise la lecture des attributs d'objets SQLAlchemy,
    # si nécessaire pour d'autres réponses.
    model_config = ConfigDict(from_attributes=True)



