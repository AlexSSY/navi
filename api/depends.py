import os
from fastapi import Header
from fastapi import HTTPException
from aiogram.utils.web_app import safe_parse_webapp_init_data


async def get_telegram_user_id(init_data: str = Header(..., alias="X-Telegram-Init-Data")) -> int:
    """
    Dependency для FastAPI.
    Принимает initData (строка от Telegram WebApp), валидирует и возвращает user_id.
    """
    try:
        parsed = safe_parse_webapp_init_data(os.getenv('BOT_TOKEN'), init_data)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid initData")

    if not parsed.user:
        raise HTTPException(status_code=401, detail="No user in initData")

    return parsed.user.id
