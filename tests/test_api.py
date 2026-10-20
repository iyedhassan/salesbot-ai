
# Permet de simuler des requêtes HTTP vers notre API FastAPI
# sans devoir démarrer un serveur séparément.
from fastapi.testclient import TestClient

# Importe l'application FastAPI configurée dans main.py.
from main import app

# Importe la fonction qui fournit une session SQLAlchemy aux routes
# et Base, la classe de référence de nos modèles SQLAlchemy.
from app.database import get_db, Base

# Outils nécessaires pour créer un moteur de base de données de test.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Permet de partager une seule base SQLite en mémoire
# entre les connexions utilisées pendant les tests.
from sqlalchemy.pool import StaticPool


# --------------------------------------------------
# 1. CRÉATION DE LA BASE DE DONNÉES DE TEST
# --------------------------------------------------

# Crée une base SQLite temporaire en mémoire.
# "sqlite://" signifie que les données ne sont pas stockées
# dans le fichier salesbot.db.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Crée une fabrique de sessions reliée à la base de test.
# Chaque appel à TestingSessionLocal() crée une session.
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

# Crée les tables correspondant aux modèles SQLAlchemy connus de Base.
Base.metadata.create_all(bind=test_engine)


# --------------------------------------------------
# 2. FOURNIR LA BASE DE TEST AUX ROUTES
# --------------------------------------------------

def override_get_db():
    """
    Remplace get_db pendant les tests.

    Les routes utilisent ainsi la base temporaire plutôt que
    la base SQLite habituelle du projet.
    """

    # Ouvre une nouvelle session sur la base de test.
    db = TestingSessionLocal()

    try:
        # Fournit cette session à la route testée.
        yield db
    finally:
        # Ferme toujours la session, même si une erreur survient.
        db.close()


# Indique à FastAPI d'utiliser notre fonction de test
# à chaque fois qu'une route demande Depends(get_db).
app.dependency_overrides[get_db] = override_get_db

# Crée le client qui permettra d'appeler les routes de l'API.
client = TestClient(app)


# --------------------------------------------------
# 3. RÉINITIALISER LES DONNÉES AVANT CHAQUE TEST
# --------------------------------------------------

def setup_function():
    """
    Cette fonction est exécutée avant chaque fonction de test.
    Elle remet les tables à zéro pour éviter que les tests
    dépendent des données laissées par les tests précédents.
    """

    # Supprime les tables de test.
    Base.metadata.drop_all(bind=test_engine)

    # Recrée les tables vides.
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    """
    Cette fonction est exécutée à la fin du module de tests.
    Elle retire la surcharge de dépendance ajoutée à FastAPI.
    """

    app.dependency_overrides.clear()


# --------------------------------------------------
# 4. TESTER LA ROUTE DE SANTÉ
# --------------------------------------------------

def test_health_check():
    # Simule une requête GET vers /health.
    response = client.get("/health")

    # Vérifie que l'API renvoie le statut HTTP 200.
    assert response.status_code == 200

    # Vérifie le contenu exact de la réponse JSON.
    assert response.json() == {"status": "healthy"}


# --------------------------------------------------
# 5. TESTER LA CRÉATION ET LA LECTURE D'UN PROSPECT
# --------------------------------------------------

def test_create_and_get_lead():
    # Envoie une requête POST pour créer un prospect.
    response = client.post(
        "/leads",
        json={
            "name": "Sami",
            "email": "sami@example.com",
            "company": "ABC",
        },
    )

    # Une création réussie doit renvoyer HTTP 201.
    assert response.status_code == 201

    # Récupère l'identifiant généré par la base de données.
    lead_id = response.json()["lead"]["id"]

    # Utilise cet identifiant pour lire le prospect créé.
    response = client.get(f"/leads/{lead_id}")

    # Vérifie que le prospect a bien été trouvé.
    assert response.status_code == 200

    # Vérifie que l'adresse email correspond à celle envoyée.
    assert response.json()["email"] == "sami@example.com"


# --------------------------------------------------
# 6. TESTER LA MODIFICATION D'UN PROSPECT
# --------------------------------------------------

def test_update_lead():
    # Crée d'abord un prospect pour pouvoir le modifier.
    created = client.post(
        "/leads",
        json={
            "name": "Sami",
            "email": "sami@example.com",
            "company": "ABC",
        },
    )

    # Récupère son identifiant.
    lead_id = created.json()["lead"]["id"]

    # Envoie une requête PUT avec les nouvelles valeurs.
    response = client.put(
        f"/leads/{lead_id}",
        json={
            "name": "Sami Ben Ali",
            "email": "sami.benali@example.com",
            "company": "XYZ",
        },
    )

    # Vérifie que la modification a réussi.
    assert response.status_code == 200

    # Vérifie que le nom a bien été modifié.
    assert response.json()["lead"]["name"] == "Sami Ben Ali"


# --------------------------------------------------
# 7. TESTER LA SUPPRESSION D'UN PROSPECT
# --------------------------------------------------

def test_delete_lead():
    # Crée un prospect qui sera ensuite supprimé.
    created = client.post(
        "/leads",
        json={
            "name": "Sami",
            "email": "sami@example.com",
            "company": "ABC",
        },
    )

    # Récupère son identifiant.
    lead_id = created.json()["lead"]["id"]

    # Demande la suppression du prospect.
    response = client.delete(f"/leads/{lead_id}")

    # Vérifie que la suppression a réussi.
    assert response.status_code == 200

    # Essaie de retrouver le prospect supprimé.
    response = client.get(f"/leads/{lead_id}")

    # L'API doit répondre 404, car le prospect n'existe plus.
    assert response.status_code == 404



def test_create_lead_with_invalid_email():
    """
    Vérifie que l'API refuse un prospect dont l'email
    ne respecte pas le format attendu.
    """

    # Envoie une requête POST avec un email invalide.
    response = client.post(
        "/leads",
        json={
            "name": "Sami",
            "email": "email-invalide",
            "company": "ABC",
        },
    )

    # FastAPI doit refuser les données avec le statut HTTP 422.
    assert response.status_code == 422

    # Vérifie que la réponse contient des informations d'erreur.
    assert "detail" in response.json()


def test_get_nonexistent_lead():
    """
    Vérifie qu'une recherche avec un ID inexistant
    renvoie le code HTTP 404 (Not Found).
    """
    response = client.get("/leads/999999")

    # 404 signifie que le prospect demandé n'existe pas.
    assert response.status_code == 404


def test_update_nonexistent_lead():
    """
    Vérifie qu'on ne peut pas modifier un prospect
    qui n'existe pas dans la base de données.
    """
    response = client.put(
        "/leads/999999",
        json={
            "name": "Sami",
            "email": "sami@example.com",
            "company": "ABC",
        },
    )

    # L'API doit signaler que le prospect est introuvable.
    assert response.status_code == 404


def test_delete_nonexistent_lead():
    """
    Vérifie qu'on ne peut pas supprimer un prospect
    qui n'existe pas dans la base de données.
    """
    response = client.delete("/leads/999999")

    # L'API doit renvoyer 404, sans planter.
    assert response.status_code == 404

def test_create_lead_with_duplicate_email():
    """
    Vérifie que l'API refuse deux prospects avec la même adresse e-mail.
    """

    # Crée un premier prospect : cette opération doit réussir.
    first_response = client.post(
        "/leads",
        json={
            "name": "Sami",
            "email": "duplicate@example.com",
            "company": "ABC",
        },
    )

    assert first_response.status_code == 201

    # Essaie de créer un second prospect avec le même e-mail.
    second_response = client.post(
        "/leads",
        json={
            "name": "Amira",
            "email": "duplicate@example.com",
            "company": "XYZ",
        },
    )

    # HTTP 409 signifie que la requête entre en conflit avec une donnée existante.
    assert second_response.status_code == 409

    # Vérifie que l'API explique la cause du refus.
    assert second_response.json()["detail"] == (
        "A lead with this email already exists"
    )
