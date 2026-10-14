from fastapi import FastAPI

from app.config import APP_DESCRIPTION, APP_NAME, APP_VERSION
from app.routes import router

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

app.include_router(router)


