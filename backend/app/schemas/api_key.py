from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class APIKeyCreate(BaseModel):
    name: str

class APIKeyOut(BaseModel):
    id: UUID
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class APIKeyNew(APIKeyOut):
    api_key: str
