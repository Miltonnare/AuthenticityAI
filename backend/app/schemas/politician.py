from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class PoliticianBase(BaseModel):
    first_name: str
    last_name: str
    party: str
    current_office: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None

class PoliticianCreate(PoliticianBase):
    pass

class PoliticianUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    party: Optional[str] = None
    current_office: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None

class PoliticianOut(PoliticianBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
