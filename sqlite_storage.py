import sqlite3
from telethon.sessions import StringSession


import sqlite3
from telethon.sessions import StringSession

class NaviSQLiteSession(StringSession):
    def __init__(self, db: sqlite3.Connection, telegram_user_id: int, phone_number: str):
        # важно: если хочешь, чтобы Telethon загрузил состояние — передай строку из БД в super().__init__(...)
        existing_session = self._get_existing_session(db, telegram_user_id, phone_number)
        super().__init__(existing_session)
        self.db = db
        self.telegram_user_id = telegram_user_id
        self.phone_number = phone_number

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.save()

    def _get_existing_session(self, db, telegram_user_id, phone_number) -> str:
        """Читает строку из базы при инициализации"""
        db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER,
                phone_number TEXT,
                session TEXT,
                PRIMARY KEY (user_id, phone_number)
            )
        """)
        db.commit()

        cursor = db.execute(
            "SELECT session FROM sessions WHERE user_id = ? AND phone_number = ?",
            (telegram_user_id, phone_number)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else ""

    def save(self):
        """Сохраняет текущее состояние StringSession в БД"""
        data = super().save()
        if not data:
            return  # нечего сохранять

        self.db.execute(
            """
            INSERT INTO sessions (user_id, phone_number, session)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, phone_number)
            DO UPDATE SET session = excluded.session
            """,
            (self.telegram_user_id, self.phone_number, data)
        )
        self.db.commit()



import base64
from telethon.sessions import MemorySession
from telethon.crypto import AuthKey

class AuthKeySession(MemorySession):
    def __init__(self, db, user_id: int, phone_number: str):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.phone_number = phone_number

    @property
    def auth_key(self):
        """Загружаем auth_key из БД"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS telegram_auth_keys (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT,
                auth_key TEXT
            )
        """)
        self.db.commit()

        cursor = self.db.execute(
            "SELECT auth_key FROM telegram_auth_keys WHERE user_id = ?", (self.user_id,)
        )
        row = cursor.fetchone()
        cursor.close()

        if row and row[0]:
            data = base64.b64decode(row[0])
            self.auth_key = AuthKey(data)
            print(f"✅ Loaded auth_key for {self.phone_number}")

    @auth_key.setter
    def auth_key(self, value):
        self._auth_key = value

    def save(self):
        """Сохраняем auth_key в БД"""
        breakpoint()
        if not self.auth_key:
            return

        encoded = base64.b64encode(self.auth_key.key).decode()

        self.db.execute("""
            INSERT INTO telegram_auth_keys (user_id, phone_number, auth_key)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET auth_key = excluded.auth_key
        """, (self.user_id, self.phone_number, encoded))
        self.db.commit()

        print(f"💾 Saved auth_key for {self.phone_number}")
