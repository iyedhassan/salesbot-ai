
# Importe Session pour interagir avec la base de données.
from sqlalchemy.orm import Session

# Importe le modèle SQLAlchemy qui représente un prospect en base.
from app.models.lead_db import LeadDB


def get_lead_by_id(db: Session, lead_id: int) -> LeadDB | None:
    """
    Recherche un prospect à partir de son identifiant.

    Args:
        db: session de connexion à la base de données.
        lead_id: identifiant du prospect recherché.

    Returns:
        Le prospect trouvé, ou None s'il n'existe pas.
    """

    # Recherche le prospect dont l'identifiant correspond.
    # first() renvoie le premier résultat, ou None si aucun résultat n'existe.
    return (
        db.query(LeadDB)
        .filter(LeadDB.id == lead_id)
        .first()
    )


def get_all_leads(db: Session) -> list[LeadDB]:
    """
    Récupère tous les prospects enregistrés.

    Args:
        db: session de connexion à la base de données.

    Returns:
        Une liste de prospects. La liste est vide si aucun prospect n'existe.
    """

    # Interroge la table leads et récupère tous les prospects.
    return db.query(LeadDB).all()


def update_lead(
    db: Session,
    lead_id: int,
    name: str,
    email: str,
    company: str | None,
) -> LeadDB | None:
    """
    Met à jour un prospect.

    Renvoie None si le prospect n'existe pas.
    Déclenche ValueError si l'email est déjà utilisé.
    """

    # Recherche le prospect à modifier.
    lead = get_lead_by_id(db, lead_id)

    # Si le prospect n'existe pas, signale son absence.
    if lead is None:
        return None

    # Vérifie si un autre prospect utilise déjà cet email.
    existing_lead = (
        db.query(LeadDB)
        .filter(LeadDB.email == email, LeadDB.id != lead_id)
        .first()
    )

    # Refuse l'email s'il appartient à un autre prospect.
    if existing_lead is not None:
        raise ValueError("A lead with this email already exists")

    # Applique les nouvelles valeurs.
    lead.name = name
    lead.email = email
    lead.company = company

    try:
        # Enregistre les changements dans la base de données.
        db.commit()
    except IntegrityError:
        # Annule la transaction si la base refuse les changements.
        db.rollback()

        # Convertit l'erreur de base en erreur métier compréhensible.
        raise ValueError("A lead with this email already exists")

    # Recharge les données enregistrées.
    db.refresh(lead)

    # Renvoie le prospect modifié.
    return lead

def delete_lead(db: Session, lead_id: int) -> LeadDB | None:
    """Supprime un prospect et renvoie ses anciennes données."""

    # Recherche le prospect avant de le supprimer.
    lead = get_lead_by_id(db, lead_id)

    # Si le prospect n'existe pas, renvoie None.
    if lead is None:
        return None

    # Supprime le prospect de la session SQLAlchemy.
    db.delete(lead)

    # Valide la suppression dans la base de données.
    db.commit()

    # Renvoie l'objet pour permettre à la route de construire sa réponse.
    return lead