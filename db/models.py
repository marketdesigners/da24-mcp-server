import uuid
import pyodbc

class ApiKeyRepository:
    def __init__(self, conn: pyodbc.Connection):
        self._conn = conn

    def get_active_key(self, key: str) -> dict | None:
        with self._conn.cursor() as cursor:
            cursor.execute(
                "SELECT [key], name, is_active, usage_count "
                "FROM mcp_api_keys WHERE [key] = ? AND is_active = 1",
                key,
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {"key": row[0], "name": row[1], "is_active": row[2], "usage_count": row[3]}

    def create_key(self, name: str) -> dict:
        new_key = str(uuid.uuid4())
        with self._conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO mcp_api_keys ([key], name) "
                "OUTPUT INSERTED.[key], INSERTED.name, INSERTED.created_at "
                "VALUES (?, ?)",
                new_key, name,
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("INSERT into mcp_api_keys returned no row")
        self._conn.commit()
        return {"key": row[0], "name": row[1], "created_at": str(row[2])}

    def list_keys(self) -> list[dict]:
        with self._conn.cursor() as cursor:
            cursor.execute(
                "SELECT [key], name, is_active, usage_count, created_at, last_used_at "
                "FROM mcp_api_keys ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
        return [
            {
                "key": r[0], "name": r[1], "is_active": bool(r[2]),
                "usage_count": r[3], "created_at": str(r[4]), "last_used_at": str(r[5]) if r[5] else None,
            }
            for r in rows
        ]

    def set_active(self, key: str, is_active: bool) -> bool:
        with self._conn.cursor() as cursor:
            cursor.execute(
                "UPDATE mcp_api_keys SET is_active = ? WHERE [key] = ?",
                1 if is_active else 0, key,
            )
            updated = cursor.rowcount > 0
        self._conn.commit()
        return updated

    def update_usage(self, key: str) -> None:
        with self._conn.cursor() as cursor:
            cursor.execute(
                "UPDATE mcp_api_keys "
                "SET usage_count = usage_count + 1, last_used_at = GETDATE() "
                "WHERE [key] = ?",
                key,
            )
        self._conn.commit()
