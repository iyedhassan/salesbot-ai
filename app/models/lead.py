from pydantic import BaseModel, EmailStr


class Lead(BaseModel):
    name: str
    email: EmailStr
    company: str | None = None
