
# Importe les outils Pydantic pour valider et nettoyer les données.
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator


class Lead(BaseModel):
    """Valide les informations d'un prospect SalesBot AI."""

    # Supprime les espaces inutiles avant et après chaque chaîne.
    model_config = ConfigDict(str_strip_whitespace=True)

    # Nom obligatoire du prospect.
    name: str

    # Adresse e-mail obligatoire et valide.
    email: EmailStr

    # Entreprise facultative.
    company: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Refuse un nom vide ou composé uniquement d'espaces."""

        # Vérifie que le nom contient au moins un caractère.
        if not value:
            raise ValueError("Name cannot be empty")

        return value

    @field_validator("company")
    @classmethod
    def normalize_company(cls, value: str | None) -> str | None:
        """Convertit une entreprise vide en valeur absente."""

        # Évite de stocker une chaîne vide pour une entreprise facultative.
        if value == "":
            return None

        return value
