import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from aiosqlite import Connection
from telethon.client import TelegramClient
from telethon.errors import (
    PhoneNumberInvalidError,
    BadRequestError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
)

from api.models import (
    APIResponse,
    CodeRequest,
    CodeVerifyRequest,
    PasswordVerifyRequest,
)
from api.depends import get_telegram_user_id, get_db
from api.sqlite_storage import AioNaviSQLiteSession
from dotenv import load_dotenv


load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import dotenv

    dotenv.load_dotenv()
    yield


app = FastAPI(debug=True, lifespan=lifespan)


origins = [
    "*",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.2:3000",
    "http://apinka.duckdns.org",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def phones(
    telegram_user_id: int = Depends(get_telegram_user_id),
    db: Connection = Depends(get_db),
):
    cursor = await db.execute(
        "SELECT phone_number FROM sessions WHERE user_id=? AND authenticated=?",
        (telegram_user_id, 1),
    )
    print(telegram_user_id)
    raw = await cursor.fetchall()
    return [i[0] for i in raw]


@app.post("/code-request", response_model=APIResponse)
async def code_request(
    telegram_user_id: int = Depends(get_telegram_user_id),
    db: Connection = Depends(get_db),
    code_request: CodeRequest = Body(...),
):
    async with await AioNaviSQLiteSession.create(
        db, telegram_user_id, code_request.phone_number.replace("+", "")
    ) as session_storage:
        client = TelegramClient(session_storage, API_ID, API_HASH)
        await client.connect()

        if not await client.is_user_authorized():
            try:
                sent_code = await client.send_code_request(code_request.phone_number)
                data = {
                    "phone_code_hash": sent_code.phone_code_hash,
                    "timeout": sent_code.timeout,
                }
                return APIResponse(success=True, data=data, next="code")

            except PhoneNumberInvalidError:
                print("❌ Invalid phone number.")
                await client.disconnect()
                return APIResponse(
                    success=False, error="Phone number invalid.", next="phone"
                )
            except BadRequestError as e:
                print(f"{e.__class__.__name__}: {e.code} {e.message}")
                await client.disconnect()
                return APIResponse(
                    success=False, error="Bad Request Error.", next="phone"
                )
        else:
            return APIResponse(success=True, next="final")

    return APIResponse(success=False, error="Phone number invalid.", next="phone")


@app.post("/code-verify", response_model=APIResponse)
async def code_verify(
    telegram_user_id: int = Depends(get_telegram_user_id),
    db: Connection = Depends(get_db),
    code_verify_request: CodeVerifyRequest = Body(...),
):
    async with await AioNaviSQLiteSession.create(
        db, telegram_user_id, code_verify_request.phone_number.replace("+", "")
    ) as session_storage:
        client = TelegramClient(session_storage, API_ID, API_HASH)
        await client.connect()
        try:
            await client.sign_in(
                phone=code_verify_request.phone_number.replace("+", ""),
                code=code_verify_request.code,
                phone_code_hash=code_verify_request.phone_code_hash,
            )
            print("✅ Authorized with code.")
            await client.disconnect()
            return APIResponse(success=True, next="final")
        except SessionPasswordNeededError:
            print("🔐 2FA password required.")
            await client.disconnect()
            return APIResponse(success=False, next="password")
        except BadRequestError as e:
            print(f"{e.__class__.__name__}: {e.code} {e.message}")
            await client.disconnect()
            return APIResponse(success=False, error="Bad Request.", next="code")


@app.post("/password-verify", response_model=APIResponse)
async def password_verify(
    telegram_user_id: int = Depends(get_telegram_user_id),
    db: Connection = Depends(get_db),
    password_verify_request: PasswordVerifyRequest = Body(...),
):
    async with await AioNaviSQLiteSession.create(
        db, telegram_user_id, code_request.phone_number.replace("+", "")
    ) as session_storage:
        client = TelegramClient(session_storage, API_ID, API_HASH)
        await client.connect()

        try:
            await client.sign_in(password=password_verify_request.password)
            print("✅ Authorized with password.")
            await client.disconnect()
            await session_storage.makeAuthenticated()
            return APIResponse(success=True, next="final")
        except PasswordHashInvalidError:
            print("❌ Invalid 2FA password.")
            await client.disconnect()
            return APIResponse(success=False, next="password")


@app.post("/spam")
async def spam(
    telegram_user_id: int = Depends(get_telegram_user_id),
    db: Connection = Depends(get_db),
    file: UploadFile = File(...),
    text: str = Form(...),
):
    os.makedirs("uploads", exist_ok=True)
    path = f"uploads/{file.filename}"

    # сохраняем файл
    with open(path, "wb") as f:
        f.write(await file.read())

    cursor = await db.execute(
        "SELECT phone_number FROM sessions WHERE user_id=? AND authenticated=?",
        (telegram_user_id, 1),
    )
    raw_phone_list = await cursor.fetchall()
    phone_list = [i[0] for i in raw_phone_list]

    for phone_number in phone_list:
        async with await AioNaviSQLiteSession.create(
            db, telegram_user_id, phone_number
        ) as session_storage:
            client = TelegramClient(session_storage, API_ID, API_HASH)
            await client.connect()

            # рассылаем всем контактам
            count = 0
            for user in await client.get_dialogs():
                try:
                    # await client.send_file(user.id, path, caption=text)
                    print(f"Send To: {user.name}")
                    count += 1
                except Exception as e:
                    print(f"Ошибка при отправке {user.name}: {e}")

            return {"status": "ok", "sent": count, "text": text}
