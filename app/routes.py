from fastapi import APIRouter

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
