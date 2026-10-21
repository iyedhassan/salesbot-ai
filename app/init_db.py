
# Importe le moteur, la base déclarative et les modèles SQLAlchemy.
from app.database import Base, engine
from app.models.lead_db import LeadDB

# Crée les tables manquantes dans la base de données.
# Les tables déjà existantes ne sont pas recréées.
Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    # Affiche un message lorsque le script est exécuté directement.
    print("Initialisation de la base de données terminée.")
