
"""Tableau de bord SalesBot AI : gestion complète des prospects."""

"""Configuration du tableau de bord SalesBot AI."""

# Permet de lire les variables d'environnement du système.
import os

# Bibliothèque utilisée pour communiquer avec l'API FastAPI.
import requests

# Bibliothèque utilisée pour afficher le tableau de bord.
import streamlit as st

# Adresse de l'API :
# - en local, on utilise http://127.0.0.1:8000 par défaut ;
# - en production, on définit SALESBOT_API_URL avec l'adresse publique.
# strip() retire les espaces et rstrip("/") évite les doubles barres.
API_URL = os.getenv(
    "SALESBOT_API_URL",
    "http://127.0.0.1:8000",
).strip().rstrip("/")


# Configuration générale de la page.
st.set_page_config(
    page_title="SalesBot AI",
    page_icon="📊",
    layout="wide",
)

st.title("📊 SalesBot AI")
st.caption("Gestion et priorisation des prospects")

# --------------------------------------------------
# 1. AJOUTER UN PROSPECT
# --------------------------------------------------

with st.expander("➕ Ajouter un prospect"):
    with st.form("create_lead_form"):
        new_name = st.text_input("Nom complet")
        new_email = st.text_input("Adresse e-mail")
        new_company = st.text_input("Entreprise (facultatif)")

        create_clicked = st.form_submit_button("Créer le prospect")

    if create_clicked:
        if not new_name.strip() or not new_email.strip():
            st.error("Le nom et l'e-mail sont obligatoires.")
        else:
            try:
                response = requests.post(
                    f"{API_URL}/leads",
                    json={
                        "name": new_name.strip(),
                        "email": new_email.strip(),
                        "company": new_company.strip() or None,
                    },
                    timeout=5,
                )

                if response.status_code == 201:
                    st.success("Prospect créé avec succès.")
                    st.rerun()
                elif response.status_code == 409:
                    st.error("Cette adresse e-mail existe déjà.")
                elif response.status_code == 422:
                    st.error("Données invalides. Vérifie les champs.")
                else:
                    st.error(f"Erreur API : {response.status_code}")

            except requests.RequestException:
                st.error("API inaccessible. Vérifie le serveur FastAPI.")

# --------------------------------------------------
# 2. FILTRER ET CHARGER LES PROSPECTS
# --------------------------------------------------

st.divider()

priority_filter = st.selectbox(
    "Filtrer par priorité",
    ["Toutes", "High", "Medium", "Low"],
)

try:
    params = {}

    if priority_filter != "Toutes":
        params["priority"] = priority_filter

    # Récupère les prospects et leur score.
    response = requests.get(
        f"{API_URL}/leads/scored",
        params=params,
        timeout=5,
    )
    response.raise_for_status()
    leads = response.json()

    # Récupère les statistiques globales.
    stats_response = requests.get(f"{API_URL}/stats", timeout=5)
    stats_response.raise_for_status()
    stats = stats_response.json()

    # Affiche les indicateurs.
    col1, col2, col3 = st.columns(3)
    col1.metric("Total des prospects", stats["total_leads"])
    col2.metric(
        "Priorité élevée affichée",
        sum(lead["priority"] == "High" for lead in leads),
    )
    col3.metric("Prospects affichés", len(leads))

    # Affiche la liste.
    st.subheader("📋 Prospects")

    if leads:
        st.dataframe(
            [
                {
                    "ID": lead["lead_id"],
                    "Nom": lead["name"],
                    "E-mail": lead["email"],
                    "Entreprise": lead["company"] or "Non renseignée",
                    "Score": lead["score"],
                    "Priorité": lead["priority"],
                }
                for lead in leads
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Aucun prospect trouvé.")

    # --------------------------------------------------
    # 3. MODIFIER UN PROSPECT
    # --------------------------------------------------

    st.divider()
    st.subheader("✏️ Modifier un prospect")

    if leads:
        # Sélectionne un prospect à modifier.
        lead_options = {
            f'{lead["lead_id"]} — {lead["name"]}': lead
            for lead in leads
        }

        selected_label = st.selectbox(
            "Choisir un prospect",
            list(lead_options.keys()),
            key="edit_lead_selection",
        )
        selected_lead = lead_options[selected_label]

        with st.form("edit_lead_form"):
            edit_name = st.text_input(
                "Nom",
                value=selected_lead["name"],
            )
            edit_email = st.text_input(
                "E-mail",
                value=selected_lead["email"],
            )
            edit_company = st.text_input(
                "Entreprise",
                value=selected_lead["company"] or "",
            )

            update_clicked = st.form_submit_button("Enregistrer les modifications")

        if update_clicked:
            if not edit_name.strip() or not edit_email.strip():
                st.error("Le nom et l'e-mail sont obligatoires.")
            else:
                try:
                    update_response = requests.put(
                        f'{API_URL}/leads/{selected_lead["lead_id"]}',
                        json={
                            "name": edit_name.strip(),
                            "email": edit_email.strip(),
                            "company": edit_company.strip() or None,
                        },
                        timeout=5,
                    )

                    if update_response.status_code == 200:
                        st.success("Prospect modifié avec succès.")
                        st.rerun()
                    elif update_response.status_code == 409:
                        st.error("Cette adresse e-mail est déjà utilisée.")
                    elif update_response.status_code == 422:
                        st.error("Les données envoyées sont invalides.")
                    else:
                        st.error(
                            f"Échec de modification : "
                            f"HTTP {update_response.status_code}"
                        )

                except requests.RequestException:
                    st.error("Impossible de contacter l'API.")

    # --------------------------------------------------
    # 4. SUPPRIMER UN PROSPECT
    # --------------------------------------------------

    st.divider()
    st.subheader("🗑️ Supprimer un prospect")

    if leads:
        delete_options = {
            f'{lead["lead_id"]} — {lead["name"]}': lead
            for lead in leads
        }

        delete_label = st.selectbox(
            "Choisir le prospect à supprimer",
            list(delete_options.keys()),
            key="delete_lead_selection",
        )
        delete_lead = delete_options[delete_label]

        # Demande une confirmation avant une suppression définitive.
        confirm_delete = st.checkbox(
            f'Je confirme la suppression de « {delete_lead["name"]} »',
            key="confirm_delete",
        )

        if st.button(
            "Supprimer définitivement",
            type="primary",
            disabled=not confirm_delete,
        ):
            try:
                delete_response = requests.delete(
                    f'{API_URL}/leads/{delete_lead["lead_id"]}',
                    timeout=5,
                )

                if delete_response.status_code in (200, 204):
                    st.success("Prospect supprimé.")
                    st.rerun()
                elif delete_response.status_code == 404:
                    st.error("Ce prospect n'existe plus.")
                else:
                    st.error(
                        f"Échec de suppression : "
                        f"HTTP {delete_response.status_code}"
                    )

            except requests.RequestException:
                st.error("Impossible de contacter l'API.")

except requests.RequestException:
    st.error(
        "Impossible de contacter l'API. Lance-la avec : "
        "uvicorn main:app --reload"
    )
except (KeyError, ValueError) as exc:
    st.error(f"Réponse inattendue de l'API : {exc}")
