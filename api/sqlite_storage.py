import aiosqlite
from telethon.sessions import StringSession


class AioNaviSQLiteSession(StringSession):
    def __init__(
        self,
        db: aiosqlite.Connection,
        telegram_user_id: int,
        phone_number: str,
        existing_session: str,
    ):
        super().__init__(existing_session)
        self.db = db
        self.telegram_user_id = telegram_user_id
        self.phone_number = phone_number

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.save()

    @classmethod
    async def create(
        cls, db: aiosqlite.Connection, telegram_user_id: int, phone_number: str
    ):
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER,
                phone_number TEXT,
                session TEXT,
                authenticated INTEGER,
                PRIMARY KEY (user_id, phone_number)
            )
        """)
        await db.commit()

        cursor = await db.execute(
            "SELECT session FROM sessions WHERE user_id = ? AND phone_number = ?",
            (telegram_user_id, phone_number),
        )
        row = await cursor.fetchone()
        existing_session = row[0] if row and row[0] else ""
        return cls(db, telegram_user_id, phone_number, existing_session)

    async def save(self):
        """Сохраняет текущее состояние StringSession в БД"""
        data = super().save()
        if not data:
            return  # нечего сохранять

        await self.db.execute(
            """
            INSERT INTO sessions (user_id, phone_number, session)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, phone_number)
            DO UPDATE SET session = excluded.session
            """,
            (self.telegram_user_id, self.phone_number, data),
        )
        await self.db.commit()

    async def makeAuthenticated(self):
        await self.db.execute(
            "UPDATE sessions SET authenticated=? WHERE user_id=?",
            (1, self.telegram_user_id),
        )
        await self.db.commit()
