import asyncio
import sqlite3
from telethon import TelegramClient
from telethon.errors import (
    BadRequestError,
    PasswordHashInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError
)

from sqlite_storage import AuthKeySession, NaviSQLiteSession

API_ID = 11721693
API_HASH = "e412ffeed9408ed2f3525736cf579ebf"


async def process_password(client):
    password = input("Enter password: ")

    try:
        await client.sign_in(password=password)
        print("✅ Authorized with password.")
    except PasswordHashInvalidError:
        print("❌ Invalid 2FA password.")
        await client.disconnect()


async def process_code(client, phone_number, phone_code_hash):
    code = input("Enter code: ")

    try:
        await client.sign_in(phone=phone_number, code=code, phone_code_hash=phone_code_hash)
        print("✅ Authorized with code.")
    except SessionPasswordNeededError:
        print("🔐 2FA password required.")
        await process_password(client)
    except BadRequestError as e:
        print(f"{e.__class__.__name__}: {e.code} {e.message}")
        await client.disconnect()


async def main():
    phone_number = input("Enter phone: ")
    session_phone_number = phone_number.replace('+', '')

    # session_storage = SQLiteSession(phone_number)
    with sqlite3.connect("sessions.sqlite3") as db:
        with NaviSQLiteSession(db, 1, session_phone_number) as session_storage:
            client = TelegramClient(session_storage, API_ID, API_HASH)

            await client.connect()

            if not await client.is_user_authorized():
                try:
                    sent_code = await client.send_code_request(phone_number)
                except PhoneNumberInvalidError:
                    print("❌ Invalid phone number.")
                    await client.disconnect()
                    return
                except BadRequestError as e:
                    print(f"{e.__class__.__name__}: {e.code} {e.message}")
                    await client.disconnect()
                    return

                await process_code(client, phone_number, sent_code.phone_code_hash)
            else:
                print("✅ Already authorized.")

            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
