from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message as TgMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import engine
from app.models.client import Client
from app.models.ticket import Ticket
from app.models.message import Message
from app.websocket.manager import ws_manager

router = Router()

@router.message(CommandStart())
async def cmd_start(message: TgMessage):
    await message.answer("Hello! Please describe your issue in a single message, and we will reply shortly.")


@router.message(F.text)
async def handle_client_message(message: TgMessage):
    tg_user = message.from_user

    async with AsyncSession(engine) as session:
        # 1. get or create client
        result = await session.execute(
            select(Client).where(Client.telegram_id == tg_user.id)
        )
        client = result.scalars().first()

        if not client:
            client = Client(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
            )
            session.add(client)
            await session.flush()

        # 2. open ticket or new
        result = await session.execute(
            select(Ticket).where(Ticket.client_id == client.id, Ticket.status == "open")
        )
        ticket = result.scalars().first()
        is_new_ticket = ticket is None

        if is_new_ticket:
            ticket = Ticket(client_id=client.id)
            session.add(ticket)
            await session.flush()

        # 3. save the message and document
        ticket_id = ticket.id  
        session.add(Message(ticket_id=ticket_id, sender_type="client", text=message.text))
        await session.commit()

    await ws_manager.broadcast({"type": "new_message", "ticket_id": ticket_id})

    if is_new_ticket:
        await message.answer("Your request has been received. A manager will respond shortly.")
