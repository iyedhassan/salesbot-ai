
from fastapi import FastAPI

app = FastAPI(
    title="SalesBot AI",
    description="API backend for an AI-powered sales chatbot",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Welcome iyed to SalesBot AI!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
