from pydantic import BaseModel
from pydantic import Field

class ManagerCreate(BaseModel):
    email: str
    full_name: str
    password: str = Field(min_length=8)

class ManagerRead(BaseModel):
    id: int
    email: str
    full_name: str

class ManagerLogin(BaseModel):
    email: str
    password: str