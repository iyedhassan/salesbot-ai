
"""Service qui calcule la priorité commerciale d'un prospect."""

from app.models.lead_score import LeadScore


def calculate_lead_score(lead) -> LeadScore:
    """
    Calcule un score simple sur 100 à partir des informations disponibles.

    Règles :
    - Nom renseigné : 20 points.
    - E-mail renseigné : 30 points.
    - Entreprise renseignée : 30 points.
    - E-mail professionnel (domaine différent des fournisseurs gratuits
      courants) : 20 points supplémentaires.

    Ce score est une première version basée sur des règles, pas un modèle IA.
    """

    score = 0

    # Le nom est obligatoire dans le modèle, mais on vérifie sa présence.
    if getattr(lead, "name", None) and lead.name.strip():
        score += 20

    # Vérifie la présence d'une adresse e-mail.
    email = str(getattr(lead, "email", "") or "").strip().lower()

    if email:
        score += 30

    # Une entreprise renseignée apporte des informations commerciales utiles.
    company = getattr(lead, "company", None)

    if company and company.strip():
        score += 30

    # Attribue un bonus si l'adresse n'utilise pas un fournisseur gratuit courant.
    free_email_domains = {
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "icloud.com",
        "live.com",
        "proton.me",
        "protonmail.com",
    }

    if email and "@" in email:
        domain = email.rsplit("@", 1)[1]

        if domain not in free_email_domains:
            score += 20

    # Protège le résultat pour qu'il reste toujours entre 0 et 100.
    score = min(score, 100)

    # Convertit le score en niveau de priorité.
    if score >= 80:
        priority = "High"
    elif score >= 50:
        priority = "Medium"
    else:
        priority = "Low"

    # Renvoie une réponse structurée et validée par Pydantic.
    return LeadScore(
        lead_id=lead.id,
        score=score,
        priority=priority,
    )
