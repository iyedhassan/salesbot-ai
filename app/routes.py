from fastapi import APIRouter, HTTPException
from app.models.lead import Lead
from app.storage import leads, next_lead_id
import app.storage as storage

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
def create_lead(lead: Lead):
    global next_lead_id

    lead_id = storage.next_lead_id
    storage.next_lead_id += 1

    lead_data = lead.model_dump()
    leads[lead_id] = {
        "id": lead_id,
        **lead_data,
    }

    return {
        "message": "Lead created successfully",
        "lead": leads[lead_id],
    }


@router.get("/leads")
def get_leads():
    return list(leads.values())


@router.get("/leads/{lead_id}")
def get_lead(lead_id: int):
    lead = leads.get(lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    return lead


@router.delete("/leads/{lead_id}")
def delete_lead(lead_id: int):
    lead = leads.pop(lead_id, None)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Lead not found",
        )

    return {
        "message": "Lead deleted successfully",
        "lead": lead,
    }
