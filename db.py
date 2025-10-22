import asyncio
import aiosqlite


async def create_db():
    async with aiosqlite.connect("db.sqlite3") as conn:
        await conn.execute("""
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number VARCHAR,
                    session BLOB   
                );
                """)
        await conn.commit()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "create_db":
            asyncio.run(create_db())
