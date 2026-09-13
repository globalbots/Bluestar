import os
import libsql_client

TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")


def get_client() -> libsql_client.Client:
    return libsql_client.create_client_sync(
        url=TURSO_URL,
        auth_token=TURSO_AUTH_TOKEN,
    )


async def init_db():
    """Create tables if they don't exist yet. Called once on bot startup."""
    client = get_client()
    try:
        client.batch(
            [
                """
                CREATE TABLE IF NOT EXISTS ticket_category_roles (
                    guild_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    role_id TEXT NOT NULL,
                    PRIMARY KEY (guild_id, category, role_id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    channel_id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    claimed_by TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """,
            ]
        )
        print("🗄️  Turso tables ready")
    finally:
        client.close()


async def set_category_roles(guild_id: int, category: str, role_ids: list[int]):
    client = get_client()
    try:
        client.execute(
            "DELETE FROM ticket_category_roles WHERE guild_id = ? AND category = ?",
            [str(guild_id), category],
        )
        for role_id in role_ids:
            client.execute(
                "INSERT INTO ticket_category_roles (guild_id, category, role_id) VALUES (?, ?, ?)",
                [str(guild_id), category, str(role_id)],
            )
    finally:
        client.close()


async def get_category_roles(guild_id: int, category: str) -> list[int]:
    client = get_client()
    try:
        result = client.execute(
            "SELECT role_id FROM ticket_category_roles WHERE guild_id = ? AND category = ?",
            [str(guild_id), category],
        )
        return [int(row[0]) for row in result.rows]
    finally:
        client.close()


async def create_ticket(channel_id: int, guild_id: int, user_id: int, category: str):
    client = get_client()
    try:
        client.execute(
            "INSERT INTO tickets (channel_id, guild_id, user_id, category) VALUES (?, ?, ?, ?)",
            [str(channel_id), str(guild_id), str(user_id), category],
        )
    finally:
        client.close()


async def claim_ticket(channel_id: int, claimer_id: int):
    client = get_client()
    try:
        client.execute(
            "UPDATE tickets SET claimed_by = ? WHERE channel_id = ?",
            [str(claimer_id), str(channel_id)],
        )
    finally:
        client.close()


async def get_ticket(channel_id: int):
    client = get_client()
    try:
        result = client.execute(
            "SELECT channel_id, guild_id, user_id, category, claimed_by FROM tickets WHERE channel_id = ?",
            [str(channel_id)],
        )
        if not result.rows:
            return None
        row = result.rows[0]
        return {
            "channel_id": int(row[0]),
            "guild_id": int(row[1]),
            "user_id": int(row[2]),
            "category": row[3],
            "claimed_by": int(row[4]) if row[4] else None,
        }
    finally:
        client.close()


async def delete_ticket(channel_id: int):
    client = get_client()
    try:
        client.execute("DELETE FROM tickets WHERE channel_id = ?", [str(channel_id)])
    finally:
        client.close()
