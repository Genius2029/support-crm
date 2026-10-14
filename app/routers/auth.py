from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.manager import Manager
from app.schemas.manager import ManagerCreate, ManagerRead, ManagerLogin
from app.core.security import hash_password, verify_password, create_access_token, get_current_manager

from sqlmodel import select

router = APIRouter()


@router.post("/register", response_model=ManagerRead, dependencies=[Depends(get_current_manager)])
async def register_manager(data: ManagerCreate, session: AsyncSession = Depends(get_session)):
    new_manager = Manager(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    session.add(new_manager)
    await session.commit()
    await session.refresh(new_manager)
    return new_manager

@router.post("/login")
async def login_manager(data: ManagerLogin, session: AsyncSession = Depends(get_session)):
    query = select(Manager).where(Manager.email == data.email)
    result = await session.execute(query)
    manager = result.first()

    if not manager or not verify_password(data.password, manager[0].hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(manager_id=manager[0].id)
    return {"access_token": token, "token_type": "bearer"}