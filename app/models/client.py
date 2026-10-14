from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger
from typing import Optional

class Client(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    telegram_id: int = Field(sa_column=Column(BigInteger, unique=True, index=True))
    username: Optional[str] = None
    first_name: str