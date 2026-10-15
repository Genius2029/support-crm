import os

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.core.security import create_access_token, hash_password
from app.database import get_session
from app.main import app
from app.models.client import Client
from app.models.manager import Manager
from app.models.ticket import Ticket

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
assert TEST_DATABASE_URL and TEST_DATABASE_URL.endswith("_test"), (
    "TEST_DATABASE_URL must point to a database whose name ends with _test"
)

MANAGER_EMAIL = "boss@test.com"
MANAGER_PASSWORD = "secret123"


@pytest.fixture
async def engine():
    test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def api(engine):
    async def override_get_session():
        async with AsyncSession(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def manager_account(engine):
    async with AsyncSession(engine) as session:
        manager = Manager(
            email=MANAGER_EMAIL,
            full_name="Test Boss",
            hashed_password=hash_password(MANAGER_PASSWORD),
        )
        session.add(manager)
        await session.flush()
        manager_id = manager.id
        await session.commit()
    return {"id": manager_id, "email": MANAGER_EMAIL, "password": MANAGER_PASSWORD}


@pytest.fixture
def auth_headers(manager_account):
    token = create_access_token(manager_id=manager_account["id"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def ticket_id(engine):
    async with AsyncSession(engine) as session:
        client = Client(telegram_id=111222333, username="tester", first_name="Test Client")
        session.add(client)
        await session.flush()

        ticket = Ticket(client_id=client.id)
        session.add(ticket)
        await session.flush()
        new_ticket_id = ticket.id

        await session.commit()
    return new_ticket_id