
from app.database import Base, engine
from app.models.lead_db import LeadDB

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
