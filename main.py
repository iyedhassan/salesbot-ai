
# Importe FastAPI pour créer l'application web.
from fastapi import FastAPI

# Importe les informations de configuration du projet.
from app.config import APP_DESCRIPTION, APP_NAME, APP_VERSION

# Importe le routeur qui contient les endpoints de l'API.
from app.routes import router

# Crée l'application FastAPI avec ses informations descriptives.
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

# Enregistre toutes les routes définies dans app/routes.py.
app.include_router(router)
