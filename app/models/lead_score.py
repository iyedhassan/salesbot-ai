
"""Modèle de réponse pour le score de priorité d'un prospect."""

from pydantic import BaseModel, Field


class LeadScore(BaseModel):
    """Représente le score et le niveau de priorité d'un prospect."""

    # Identifiant du prospect dans la base de données.
    lead_id: int

    # Score numérique compris entre 0 et 100.
    score: int = Field(ge=0, le=100)

    # Niveau de priorité calculé à partir du score.
    priority: str
