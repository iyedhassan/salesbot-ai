
# Importe Session pour interagir avec la base de données.
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Importe le modèle SQLAlchemy représentant un prospect.
from app.models.lead_db import LeadDB

# Importe le modèle qui définit la réponse des statistiques.
from app.models.lead_stats import LeadStats

# Importe or_ pour rechercher dans plusieurs colonnes.
from sqlalchemy import or_

def get_lead_by_id(db: Session, lead_id: int) -> LeadDB | None:
    """Recherche un prospect par son identifiant."""

    # Renvoie le prospect trouvé, ou None s'il n'existe pas.
    return (
        db.query(LeadDB)
        .filter(LeadDB.id == lead_id)
        .first()
    )


def get_all_leads(db: Session) -> list[LeadDB]:
    """Récupère tous les prospects enregistrés."""

    # Renvoie la liste des prospects présents dans la base.
    return db.query(LeadDB).all()


def get_lead_stats(db: Session) -> LeadStats:
    """
    Calcule les statistiques des prospects enregistrés.

    Un prospect est considéré comme ayant une entreprise
    si company n'est ni None ni une chaîne vide.
    """

    # Compte le nombre total de prospects dans la base.
    total_leads = db.query(LeadDB).count()

    # Compte les prospects dont l'entreprise est renseignée.
    leads_with_company = (
        db.query(LeadDB)
        .filter(
            LeadDB.company.is_not(None),
            LeadDB.company != "",
        )
        .count()
    )

    # Calcule le nombre de prospects sans entreprise renseignée.
    leads_without_company = total_leads - leads_with_company

    # Construit une réponse validée par Pydantic.
    return LeadStats(
        total_leads=total_leads,
        leads_with_company=leads_with_company,
        leads_without_company=leads_without_company,
    )


def update_lead(
    db: Session,
    lead_id: int,
    name: str,
    email: str,
    company: str | None,
) -> LeadDB | None:
    """Met à jour un prospect."""

    # Recherche le prospect à modifier.
    lead = get_lead_by_id(db, lead_id)

    # Renvoie None si le prospect n'existe pas.
    if lead is None:
        return None

    # Vérifie si un autre prospect utilise déjà cet email.
    existing_lead = (
        db.query(LeadDB)
        .filter(
            LeadDB.email == email,
            LeadDB.id != lead_id,
        )
        .first()
    )

    # Refuse un email déjà utilisé par un autre prospect.
    if existing_lead is not None:
        raise ValueError("A lead with this email already exists")

    # Applique les nouvelles valeurs.
    lead.name = name
    lead.email = email
    lead.company = company

    try:
        # Enregistre les modifications dans la base.
        db.commit()
    except IntegrityError:
        # Annule la transaction si la base refuse les changements.
        db.rollback()

        # Renvoie une erreur métier compréhensible.
        raise ValueError(
            "A lead with this email already exists"
        )

    # Recharge les données depuis la base.
    db.refresh(lead)

    # Renvoie le prospect modifié.
    return lead


def delete_lead(db: Session, lead_id: int) -> LeadDB | None:
    """Supprime un prospect et renvoie ses anciennes données."""

    # Recherche le prospect avant de le supprimer.
    lead = get_lead_by_id(db, lead_id)

    # Renvoie None s'il n'existe pas.
    if lead is None:
        return None

    # Supprime le prospect.
    db.delete(lead)

    # Enregistre la suppression dans la base.
    db.commit()

    # Renvoie les anciennes données du prospect supprimé.
    return lead



def search_leads(db: Session, query: str) -> list[LeadDB]:
    """Recherche des prospects par nom, e-mail ou entreprise."""

    # Supprime les espaces superflus dans la recherche.
    search_term = query.strip()

    # Si la recherche est vide, renvoie une liste vide.
    if not search_term:
        return []

    # Ajoute les jokers SQL pour rechercher une partie du texte.
    pattern = f"%{search_term}%"

    # Recherche le texte dans le nom, l'e-mail ou l'entreprise.
    return (
        db.query(LeadDB)
        .filter(
            or_(
                LeadDB.name.ilike(pattern),
                LeadDB.email.ilike(pattern),
                LeadDB.company.ilike(pattern),
            )
        )
        .all()
    )
