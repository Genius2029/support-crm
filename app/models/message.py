from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

class Message(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id")
    sender_type: str
    text: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())