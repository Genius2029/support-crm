from aiogram import Bot
from aiogram.exceptions import TelegramAPIError


async def test_tickets_require_token(api):
    response = await api.get("/tickets")

    assert response.status_code in (401, 403)


async def test_ticket_list_shows_client_name(api, auth_headers, ticket_id):
    response = await api.get("/tickets", headers=auth_headers)

    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["client_name"] == "Test Client"


async def test_reply_is_sent_to_telegram_and_saved(api, auth_headers, ticket_id, monkeypatch):
    sent = []

    async def fake_send_message(self, chat_id, text, **kwargs):
        sent.append({"chat_id": chat_id, "text": text})

    monkeypatch.setattr(Bot, "send_message", fake_send_message)

    response = await api.post(
        f"/tickets/{ticket_id}/messages",
        json={"text": "Hello!"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert sent == [{"chat_id": 111222333, "text": "Hello!"}]

    messages = await api.get(f"/tickets/{ticket_id}/messages", headers=auth_headers)
    assert [m["text"] for m in messages.json()] == ["Hello!"]


async def test_failed_delivery_saves_nothing(api, auth_headers, ticket_id, monkeypatch):
    async def broken_send_message(self, chat_id, text, **kwargs):
        raise TelegramAPIError(method=None, message="bot was blocked by the user")

    monkeypatch.setattr(Bot, "send_message", broken_send_message)

    response = await api.post(
        f"/tickets/{ticket_id}/messages",
        json={"text": "Hello!"},
        headers=auth_headers,
    )

    assert response.status_code == 502

    messages = await api.get(f"/tickets/{ticket_id}/messages", headers=auth_headers)
    assert messages.json() == []