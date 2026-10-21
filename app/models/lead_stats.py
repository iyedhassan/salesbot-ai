
# Importe BaseModel pour définir la structure de la réponse API.
from pydantic import BaseModel


class LeadStats(BaseModel):
    """
    Définit les statistiques renvoyées par l'API SalesBot AI.
    """

    # Nombre total de prospects enregistrés.
    total_leads: int

    # Nombre de prospects dont le champ company est renseigné.
    leads_with_company: int

    # Nombre de prospects dont le champ company est absent ou vide.
    leads_without_company: int

# Importe BaseModel pour définir la structure de la réponse API.
from pydantic import BaseModel


class LeadStats(BaseModel):
    """
    Définit les statistiques renvoyées par l'API SalesBot AI.
    """

    # Nombre total de prospects enregistrés.
    total_leads: int

    # Nombre de prospects dont le champ company est renseigné.
    leads_with_company: int

    # Nombre de prospects dont le champ company est absent ou vide.
    leads_without_company: int
