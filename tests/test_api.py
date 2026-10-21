
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

def test_duplicate_email_does_not_create_second_lead():
    """
    Vérifie qu'un e-mail identique ne peut pas être enregistré deux fois.
    La seconde requête doit renvoyer HTTP 409.
    """

    # Crée le premier prospect : cette requête doit réussir.
    first_response = client.post(
        "/leads",
        json={
            "name": "Sami",
            "email": "unique-check@example.com",
            "company": "ABC",
        },
    )

    # Vérifie que le premier prospect a bien été créé.
    assert first_response.status_code == 201

    # Tente de créer un second prospect avec le même e-mail.
    second_response = client.post(
        "/leads",
        json={
            "name": "Amira",
            "email": "unique-check@example.com",
            "company": "XYZ",
        },
    )

    # L'API doit renvoyer un conflit, et non une erreur serveur 500.
    assert second_response.status_code == 409

    # Vérifie que le doublon n'a pas été ajouté.
    leads_response = client.get("/leads")

    assert leads_response.status_code == 200

    # Compte les prospects possédant cet e-mail.
    matching_leads = [
        lead
        for lead in leads_response.json()
        if lead["email"] == "unique-check@example.com"
    ]

    # Un seul prospect doit exister avec cette adresse.
    assert len(matching_leads) == 1



def test_get_nonexistent_lead_returns_clear_error():
    """
    Vérifie qu'un prospect inexistant renvoie une erreur 404
    avec un message explicite.
    """

    # Recherche un identifiant qui n'existe pas.
    response = client.get("/leads/999999")

    # Vérifie le code HTTP : Not Found.
    assert response.status_code == 404

    # Vérifie que l'erreur explique le problème.
    assert response.json()["detail"] == "Lead not found"


def test_invalid_email_returns_validation_error():
    """
    Vérifie qu'un e-mail mal formé est rejeté avant
    d'être enregistré dans la base de données.
    """

    # Tente de créer un prospect avec une adresse invalide.
    response = client.post(
        "/leads",
        json={
            "name": "Sami",
            "email": "pas-une-adresse-email",
            "company": "ABC",
        },
    )

    # HTTP 422 signifie que les données reçues sont invalides.
    assert response.status_code == 422

    # FastAPI doit fournir les détails de l'erreur.
    assert "detail" in response.json()



def test_update_lead_with_duplicate_email_returns_conflict():
    """Vérifie qu'un email déjà utilisé est refusé lors d'une mise à jour."""

    # Importe le client et l'application utilisés par le projet.
    # Ce test utilise une instance locale de TestClient.
    from fastapi.testclient import TestClient
    from main import app

    # Crée un client HTTP pour envoyer des requêtes à l'API.
    # La configuration de la base de test doit être appliquée
    # comme dans les autres tests du projet.
    client = TestClient(app)

    # Crée un premier prospect.
    first_response = client.post(
        "/leads",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "company": "Company A",
        },
    )
    assert first_response.status_code == 201

    # Récupère son identifiant.
    first_lead_id = first_response.json()["lead"]["id"]

    # Crée un deuxième prospect avec un autre email.
    second_response = client.post(
        "/leads",
        json={
            "name": "Bob",
            "email": "bob@example.com",
            "company": "Company B",
        },
    )
    assert second_response.status_code == 201

    # Essaie d'attribuer à Alice l'email déjà utilisé par Bob.
    update_response = client.put(
        f"/leads/{first_lead_id}",
        json={
            "name": "Alice",
            "email": "bob@example.com",
            "company": "Company A",
        },
    )

    # Vérifie que l'API refuse la modification.
    assert update_response.status_code == 409

    # Vérifie que l'email d'Alice n'a pas changé.
    get_response = client.get(f"/leads/{first_lead_id}")
    assert get_response.status_code == 200
    assert get_response.json()["email"] == "alice@example.com"


def test_get_all_leads_returns_created_leads():
    """Vérifie que l'API renvoie tous les prospects créés."""

    # Importe le client HTTP et l'application FastAPI.
    from fastapi.testclient import TestClient
    from main import app

    # Crée un client pour envoyer des requêtes à l'API.
    client = TestClient(app)

    # Crée le premier prospect.
    first_response = client.post(
        "/leads",
        json={
            "name": "Alice",
            "email": "alice.list@example.com",
            "company": "Company A",
        },
    )
    assert first_response.status_code == 201

    # Crée le deuxième prospect.
    second_response = client.post(
        "/leads",
        json={
            "name": "Bob",
            "email": "bob.list@example.com",
            "company": "Company B",
        },
    )
    assert second_response.status_code == 201

    # Demande à l'API la liste de tous les prospects.
    response = client.get("/leads")

    # Vérifie que la requête a réussi.
    assert response.status_code == 200

    # Récupère la liste renvoyée au format JSON.
    leads = response.json()

    # Vérifie que les deux prospects sont présents.
    emails = {lead["email"] for lead in leads}
    assert "alice.list@example.com" in emails
    assert "bob.list@example.com" in emails


def test_get_all_leads_returns_empty_list():
    """Vérifie que l'API renvoie une liste vide sans prospects."""

    # Importe le client HTTP et l'application FastAPI.
    from fastapi.testclient import TestClient
    from main import app

    # Crée un client HTTP pour interroger l'API.
    client = TestClient(app)

    # Demande la liste des prospects.
    response = client.get("/leads")

    # Vérifie que la requête a réussi.
    assert response.status_code == 200

    # Vérifie que la réponse est une liste JSON vide.
    assert response.json() == []



def test_get_lead_by_id_returns_correct_lead():
    """Vérifie qu'on récupère le bon prospect par son identifiant."""

    # Importe le client HTTP et l'application FastAPI.
    from fastapi.testclient import TestClient
    from main import app

    # Crée un client HTTP pour envoyer des requêtes à l'API.
    client = TestClient(app)

    # Crée un prospect pour effectuer le test.
    create_response = client.post(
        "/leads",
        json={
            "name": "Charlie",
            "email": "charlie.get@example.com",
            "company": "Company C",
        },
    )

    # Vérifie que la création du prospect a réussi.
    assert create_response.status_code == 201

    # Récupère l'identifiant généré par la base de données.
    lead_id = create_response.json()["lead"]["id"]

    # Demande les informations de ce prospect précis.
    response = client.get(f"/leads/{lead_id}")

    # Vérifie que la requête a réussi.
    assert response.status_code == 200

    # Vérifie que l'API renvoie le bon prospect.
    lead = response.json()
    assert lead["id"] == lead_id
    assert lead["name"] == "Charlie"
    assert lead["email"] == "charlie.get@example.com"
    assert lead["company"] == "Company C"


def test_get_lead_by_id_returns_404_when_missing():
    """Vérifie que l'API renvoie 404 pour un prospect inexistant."""

    # Importe le client HTTP et l'application FastAPI.
    from fastapi.testclient import TestClient
    from main import app

    # Crée un client HTTP pour interroger l'API.
    client = TestClient(app)

    # Utilise un identifiant négatif, qui ne correspond pas à un ID normal.
    response = client.get("/leads/-1")

    # Vérifie que l'API signale l'absence du prospect.
    assert response.status_code == 404

    # Vérifie que le message d'erreur est explicite.
    assert response.json()["detail"] == "Lead not found"



def test_update_lead_persists_changes():
    """Vérifie que les modifications d'un prospect sont enregistrées."""

    # Importe le client HTTP et l'application FastAPI.
    from fastapi.testclient import TestClient
    from main import app

    # Crée un client pour envoyer des requêtes à l'API.
    client = TestClient(app)

    # Crée un prospect avec ses informations initiales.
    create_response = client.post(
        "/leads",
        json={
            "name": "David",
            "email": "david.old@example.com",
            "company": "Old Company",
        },
    )

    # Vérifie que la création a réussi.
    assert create_response.status_code == 201

    # Récupère l'identifiant du prospect créé.
    lead_id = create_response.json()["lead"]["id"]

    # Modifie les informations du prospect.
    update_response = client.put(
        f"/leads/{lead_id}",
        json={
            "name": "David Updated",
            "email": "david.new@example.com",
            "company": "New Company",
        },
    )

    # Vérifie que la mise à jour a réussi.
    assert update_response.status_code == 200

    # Relit le prospect pour vérifier les données enregistrées.
    get_response = client.get(f"/leads/{lead_id}")

    assert get_response.status_code == 200

    # Vérifie que toutes les nouvelles valeurs sont conservées.
    updated_lead = get_response.json()
    assert updated_lead["name"] == "David Updated"
    assert updated_lead["email"] == "david.new@example.com"
    assert updated_lead["company"] == "New Company"


def test_delete_lead_removes_it_from_database():
    """Vérifie qu'un prospect supprimé n'est plus accessible."""

    # Importe le client HTTP et l'application FastAPI.
    from fastapi.testclient import TestClient
    from main import app

    # Crée un client pour envoyer des requêtes à l'API.
    client = TestClient(app)

    # Crée un prospect que nous supprimerons ensuite.
    create_response = client.post(
        "/leads",
        json={
            "name": "Emma",
            "email": "emma.delete@example.com",
            "company": "Company D",
        },
    )

    # Vérifie que la création a réussi.
    assert create_response.status_code == 201

    # Récupère l'identifiant du prospect créé.
    lead_id = create_response.json()["lead"]["id"]

    # Demande la suppression du prospect.
    delete_response = client.delete(f"/leads/{lead_id}")

    # Vérifie que la suppression a réussi.
    assert delete_response.status_code == 200

    # Vérifie le message de confirmation.
    assert delete_response.json()["message"] == "Lead deleted successfully"

    # Tente de récupérer le prospect supprimé.
    get_response = client.get(f"/leads/{lead_id}")

    # L'API doit répondre 404, car le prospect n'existe plus.
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Lead not found"



def test_get_stats_returns_statistics():
    """Vérifie que l'API renvoie les statistiques attendues."""

    # Importe le client de test FastAPI.
    from fastapi.testclient import TestClient

    # Importe l'application à tester.
    from main import app

    # Crée un client HTTP pour envoyer des requêtes à l'API.
    client = TestClient(app)

    # Demande les statistiques à l'API.
    response = client.get("/stats")

    # Vérifie que la route répond avec le statut HTTP 200.
    assert response.status_code == 200

    # Convertit la réponse JSON en dictionnaire Python.
    data = response.json()

    # Vérifie la présence des trois champs attendus.
    assert "total_leads" in data
    assert "leads_with_company" in data
    assert "leads_without_company" in data

    # Vérifie que les valeurs sont des nombres entiers.
    assert isinstance(data["total_leads"], int)
    assert isinstance(data["leads_with_company"], int)
    assert isinstance(data["leads_without_company"], int)

    # Vérifie que les deux catégories couvrent le total.
    assert (
        data["leads_with_company"]
        + data["leads_without_company"]
        == data["total_leads"]
    )
