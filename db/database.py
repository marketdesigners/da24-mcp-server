import pyodbc
from config import settings

_pool: list[pyodbc.Connection] = []
_POOL_SIZE = 5

def _create_connection() -> pyodbc.Connection:
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={settings.mssql_server};"
        f"DATABASE={settings.mssql_database};"
        f"UID={settings.mssql_username};"
        f"PWD={settings.mssql_password};"
        f"Connection Timeout=5;"
    )
    return pyodbc.connect(conn_str)

def get_connection() -> pyodbc.Connection:
    if _pool:
        return _pool.pop()
    return _create_connection()

def release_connection(conn: pyodbc.Connection) -> None:
    if len(_pool) < _POOL_SIZE:
        _pool.append(conn)
    else:
        conn.close()

def init_pool() -> None:
    for _ in range(_POOL_SIZE):
        _pool.append(_create_connection())
