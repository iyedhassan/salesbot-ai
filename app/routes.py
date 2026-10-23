
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lead import Lead
from app.models.lead_db import LeadDB

# Modèle qui définit la structure des réponses contenant un prospect.
from app.models.lead_response import LeadResponse

# Modèle utilisé pour les réponses de création et de mise à jour.
from app.models.lead_operation_response import LeadOperationResponse
# Permet de détecter une violation de contrainte dans la base de données.
from sqlalchemy.exc import IntegrityError
# Importe le service qui recherche un prospect par son identifiant.
# Importe les fonctions qui gèrent les opérations sur les prospects.
# Importe les fonctions qui gèrent les opérations sur les prospects.
from app.services.lead_service import (
    get_lead_by_id,
    get_all_leads,
    get_lead_stats,
    search_leads,
    update_lead,
    delete_lead,
)

# Importe le modèle qui structure la réponse des statistiques.
from app.models.lead_stats import LeadStats

# Modèle de réponse contenant le score et la priorité.
from app.models.lead_score import LeadScore

# Service qui calcule le score commercial.
from app.services.lead_scoring import calculate_lead_score

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "Welcome to SalesBot AI!",
        "status": "running",
    }


@router.get("/health")
def health_check():
    return {"status": "healthy"}


# La création renvoie un code HTTP 201 et une réponse structurée.

@router.post("/leads", status_code=201, response_model=LeadOperationResponse)
def create_lead(lead: Lead, db: Session = Depends(get_db)):
    # Recherche si un prospect possède déjà cette adresse e-mail.
    existing_lead = (
        db.query(LeadDB)
        .filter(LeadDB.email == str(lead.email))
        .first()
    )

    # Si l'e-mail existe déjà, refuse la création avec le code HTTP 409.
    if existing_lead is not None:
        raise HTTPException(
            status_code=409,
            detail="A lead with this email already exists",
        )

    # Crée l'objet destiné à être enregistré dans la base de données.
    new_lead = LeadDB(
        name=lead.name,
        email=str(lead.email),
        company=lead.company,
    )

    # Prépare l'insertion du nouveau prospect.
    db.add(new_lead)

    try:
        # Tente d'enregistrer le prospect dans SQLite.
        db.commit()

    except IntegrityError:
        # Annule la transaction en échec pour rétablir la session SQLAlchemy.
        db.rollback()

        # Renvoie un conflit si la contrainte UNIQUE a été violée.
        raise HTTPException(
            status_code=409,
            detail="A lead with this email already exists",
        )

    # Récupère l'identifiant généré par la base de données.
    db.refresh(new_lead)

    # Renvoie une réponse structurée au client.
    return {
        "message": "Lead created successfully",
        "lead": {
            "id": new_lead.id,
            "name": new_lead.name,
            "email": new_lead.email,
            "company": new_lead.company,
        },
    }




# Renvoie la liste des prospects.
# list[LeadResponse] signifie : une liste d'objets LeadResponse.

@router.get("/leads", response_model=list[LeadResponse])
def list_leads(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Retourne une page de prospects."""

    # Refuse un décalage négatif.
    if skip < 0:
        raise HTTPException(
            status_code=422,
            detail="skip must be greater than or equal to 0",
        )

    # Limite la taille de la page pour éviter des réponses trop lourdes.
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 100",
        )

    # Récupère uniquement les prospects demandés.
    return (
        db.query(LeadDB)
        .order_by(LeadDB.id)
        .offset(skip)
        .limit(limit)
        .all()
    )



@router.get("/leads/scored")
def list_scored_leads(
    priority: str | None = None,
    db: Session = Depends(get_db),
):
    """Retourne les prospects triés par score, avec un filtre facultatif."""

    # Vérifie que la priorité demandée est autorisée.
    if priority is not None:
        priority = priority.strip().capitalize()

        if priority not in {"High", "Medium", "Low"}:
            raise HTTPException(
                status_code=422,
                detail="priority must be High, Medium, or Low",
            )

    # Récupère les prospects enregistrés.
    leads = get_all_leads(db)

    # Calcule le score et prépare les résultats.
    scored_leads = []

    for lead in leads:
        result = calculate_lead_score(lead)

        # Applique le filtre si une priorité a été demandée.
        if priority is not None and result.priority != priority:
            continue

        scored_leads.append({
            "lead_id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "score": result.score,
            "priority": result.priority,
        })

    # Classe les résultats du meilleur score au plus faible.
    scored_leads.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return scored_leads



# Renvoie un seul prospect.
# FastAPI valide la réponse avec LeadResponse.
# Recherche un prospect à partir de son identifiant.
@router.get("/leads/{lead_id}", response_model=LeadResponse)
def read_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Récupère un prospect précis depuis la base de données.

    Args:
        lead_id : identifiant du prospect demandé.
        db : session de base de données fournie par FastAPI.

    Returns:
        Le prospect trouvé.

    Raises:
        HTTPException 404 si le prospect n'existe pas.
    """

    # Délègue la recherche au service.
    lead = get_lead_by_id(db, lead_id)

    # Si le service ne trouve aucun prospect, renvoie une erreur HTTP 404.
    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # Renvoie le prospect trouvé.
    # LeadResponse définit le format de la réponse JSON.
    return lead



# Définit le code HTTP et la structure de la réponse de suppression.


@router.delete(
    "/leads/{lead_id}",
    response_model=LeadOperationResponse,
)
def delete_lead_route(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """Supprime un prospect existant."""

    # Confie la suppression au service.
    deleted_lead = delete_lead(db, lead_id)

    # Si aucun prospect ne correspond à cet identifiant, renvoie 404.
    if deleted_lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # Retourne un message et les données du prospect supprimé.
    return {
        "message": "Lead deleted successfully",
        "lead": deleted_lead,
    }


# La mise à jour renvoie une réponse structurée.

@router.put(
    "/leads/{lead_id}",
    response_model=LeadOperationResponse,
)
def update_lead_route(
    lead_id: int,
    lead: Lead,
    db: Session = Depends(get_db),
):
    """Met à jour un prospect existant."""

    try:
        # Demande au service de modifier le prospect.
        updated_lead = update_lead(
            db=db,
            lead_id=lead_id,
            name=lead.name,
            email=str(lead.email),
            company=lead.company,
        )
    except ValueError as error:
        # Renvoie HTTP 409 si l'email est déjà utilisé.
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    # Renvoie HTTP 404 si le prospect n'existe pas.
    if updated_lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # Retourne le message et le prospect modifié.
    return {
        "message": "Lead updated successfully",
        "lead": updated_lead,
    }

@router.get("/stats", response_model=LeadStats)
def get_stats(db: Session = Depends(get_db)):
    """Retourne les statistiques des prospects enregistrés."""

    # Appelle le service qui calcule les statistiques en base de données.
    return get_lead_stats(db)



@router.get("/leads/search", response_model=list[LeadResponse])
def search_leads_route(
    q: str,
    db: Session = Depends(get_db),
):
    """Recherche des prospects à partir d'un texte."""

    # Refuse une recherche vide après suppression des espaces.
    if not q.strip():
        raise HTTPException(
            status_code=422,
            detail="Search query cannot be empty",
        )

    # Retourne les prospects correspondant à la recherche.
    return search_leads(db, q)



@router.get("/leads/{lead_id}/score", response_model=LeadScore)
def get_lead_score(lead_id: int, db: Session = Depends(get_db)):
    """Calcule et retourne le score commercial d'un prospect."""

    # Recherche le prospect dans la base de données.
    lead = get_lead_by_id(db, lead_id)

    # Retourne une erreur HTTP 404 si le prospect n'existe pas.
    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    # Calcule le score puis retourne le résultat structuré.
    return calculate_lead_score(lead)
