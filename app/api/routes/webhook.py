from fastapi import APIRouter, Header, HTTPException, Request
from telegram import Update

from app.api.dependencies import get_application, get_settings

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    application = get_application()
    settings = get_settings()

    expected_secret = settings.webhook_secret_token
    if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid webhook secret token")

    payload = await request.json()
    update = Update.de_json(payload, application.bot)
    await application.process_update(update)
    return {"ok": True}
