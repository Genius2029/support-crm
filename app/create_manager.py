import asyncio
import getpass
import sys

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import hash_password
from app.database import engine
from app.models.manager import Manager


def ask_password() -> str:
    while True:
        password = getpass.getpass("Password (min 8 chars, typing is hidden): ")
        if len(password) < 8:
            print("Too short, try again.")
            continue
        if password != getpass.getpass("Repeat password: "):
            print("Passwords do not match, try again.")
            continue
        return password


async def main(email: str, full_name: str):
    password = ask_password()

    async with AsyncSession(engine) as session:
        result = await session.execute(select(Manager).where(Manager.email == email))
        manager = result.scalars().first()

        if manager:
            manager.hashed_password = hash_password(password)
            manager.full_name = full_name
            session.add(manager)
            action = "updated"
        else:
            session.add(
                Manager(email=email, full_name=full_name, hashed_password=hash_password(password))
            )
            action = "created"

        await session.commit()

    await engine.dispose()
    print(f"Manager {action}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))