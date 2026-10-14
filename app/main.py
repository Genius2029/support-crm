import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from app.database import engine
from app.models.manager import Manager
from app.models.client import Client
from app.models.ticket import Ticket
from app.models.message import Message
from app.routers.auth import router as auth_router
from app.routers.tickets import router as tickets_router
from app.routers.ws import router as ws_router
from app.bot.bot import bot, dp

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    yield
    polling_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await polling_task
    await bot.session.close()



app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(ws_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/login")
def login_page():
    return FileResponse("app/templates/login.html")


@app.get("/panel")
def panel_page():
    return FileResponse("app/templates/panel.html")


@app.get("/")
def root():
    return {"message": "Support CRM API is running"}