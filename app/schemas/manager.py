from pydantic import BaseModel

class ManagerCreate(BaseModel):
    email: str
    full_name: str
    password: str

class ManagerRead(BaseModel):
    id: int
    email: str
    full_name: str

class ManagerLogin(BaseModel):
    email: str
    password: str