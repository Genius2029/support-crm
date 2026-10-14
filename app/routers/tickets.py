from typing import Optional

from aiogram.exceptions import TelegramAPIError
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.bot.bot import bot
from app.core.security import get_current_manager
from app.database import get_session
from app.models.client import Client
from app.models.manager import Manager
from app.websocket.manager import ws_manager
from app.models.message import Message
from app.models.ticket import Ticket
from app.schemas.message import ReplyCreate

# protection for ALL endpoints in this file at once
router = APIRouter(dependencies=[Depends(get_current_manager)])


async def get_ticket_or_404(ticket_id: int, session: AsyncSession) -> Ticket:
    result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/tickets")
async def get_tickets(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    query = select(Ticket, Client).join(Client, Ticket.client_id == Client.id)
    if status:
        query = query.where(Ticket.status == status)
    query = query.order_by(Ticket.id.desc())

    result = await session.execute(query)
    return [
        {
            "id": t.id,
            "status": t.status,
            "created_at": t.created_at,
            "assigned_manager_id": t.assigned_manager_id,
            "client_name": c.first_name,
            "client_username": c.username,
        }
        for t, c in result.all()
    ]


@router.get("/tickets/{ticket_id}/messages")
async def get_ticket_messages(ticket_id: int, session: AsyncSession = Depends(get_session)):
    await get_ticket_or_404(ticket_id, session)
    result = await session.execute(
        select(Message).where(Message.ticket_id == ticket_id).order_by(Message.id)
    )
    return result.scalars().all()


@router.post("/tickets/{ticket_id}/messages")
async def reply_to_ticket(
    ticket_id: int,
    data: ReplyCreate,
    session: AsyncSession = Depends(get_session),
    manager: Manager = Depends(get_current_manager),
):
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    ticket = await get_ticket_or_404(ticket_id, session)
    if ticket.status != "open":
        raise HTTPException(status_code=400, detail="Ticket is closed")

    result = await session.execute(select(Client).where(Client.id == ticket.client_id))
    client = result.scalars().first()

    # 1. First, we send it to the client via Telegram
    try:
        await bot.send_message(chat_id=client.telegram_id, text=data.text)
    except TelegramAPIError:
        raise HTTPException(status_code=502, detail="Could not deliver the message to Telegram")

    # 2. then we save it; the first manager to respond becomes the person responsible.
    if ticket.assigned_manager_id is None:
        ticket.assigned_manager_id = manager.id
        session.add(ticket)

    new_message = Message(ticket_id=ticket.id, sender_type="manager", text=data.text)
    session.add(new_message)
    await session.commit()
    await session.refresh(new_message)
    await ws_manager.broadcast({"type": "new_message", "ticket_id": ticket_id})
    return new_message


@router.patch("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: int, session: AsyncSession = Depends(get_session)):
    ticket = await get_ticket_or_404(ticket_id, session)
    ticket.status = "closed"
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    await ws_manager.broadcast({"type": "ticket_closed", "ticket_id": ticket_id})
    return ticket