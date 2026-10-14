from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field 

class Ticket(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id")
    assigned_manager_id: Optional[int] = Field(default=None, foreign_key="manager.id")
    status: str = Field(default="open", index=True)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())