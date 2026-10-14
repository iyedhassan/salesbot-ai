
from fastapi import FastAPI

from app.config import APP_DESCRIPTION, APP_NAME, APP_VERSION

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)


@app.get("/")
def root():
    return {
        "message": "Welcome to SalesBot AI!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
