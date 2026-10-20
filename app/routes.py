
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
def get_leads(db: Session = Depends(get_db)):
    return db.query(LeadDB).all()


# Renvoie un seul prospect.
# FastAPI valide la réponse avec LeadResponse.
@router.get("/leads/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()

    # Si le prospect n'existe pas, l'API renvoie une erreur 404.
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead



# Définit le code HTTP et la structure de la réponse de suppression.
@router.delete(
    "/leads/{lead_id}",
    response_model=LeadOperationResponse,
)

def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()

    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()

    return {
        "message": "Lead deleted successfully",
        "lead": {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
        },
    }


# La mise à jour renvoie une réponse structurée.
@router.put(
    "/leads/{lead_id}",
    response_model=LeadOperationResponse,
)
def update_lead(
    lead_id: int,
    updated_data: Lead,
    db: Session = Depends(get_db),
):
    lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()

    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.name = updated_data.name
    lead.email = str(updated_data.email)
    lead.company = updated_data.company

    db.commit()
    db.refresh(lead)

    return {
        "message": "Lead updated successfully",
        "lead": {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
        },
    }

