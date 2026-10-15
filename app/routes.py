
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lead import Lead
from app.models.lead_db import LeadDB

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


@router.post("/leads", status_code=201)
def create_lead(lead: Lead, db: Session = Depends(get_db)):
    new_lead = LeadDB(
        name=lead.name,
        email=str(lead.email),
        company=lead.company,
    )

    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    return {
        "message": "Lead created successfully",
        "lead": {
            "id": new_lead.id,
            "name": new_lead.name,
            "email": new_lead.email,
            "company": new_lead.company,
        },
    }


@router.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    return db.query(LeadDB).all()


@router.get("/leads/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()

    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead


@router.delete("/leads/{lead_id}")
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


@router.put("/leads/{lead_id}")
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

