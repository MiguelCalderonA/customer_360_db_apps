"""SQL warehouse query helpers."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from databricks import sql as dbsql

from .config import get_oauth_token, get_warehouse_id, get_workspace_host


@contextmanager
def cursor():
    host = get_workspace_host().replace("https://", "").replace("http://", "").rstrip("/")
    token = get_oauth_token()
    http_path = f"/sql/1.0/warehouses/{get_warehouse_id()}"
    with dbsql.connect(server_hostname=host, http_path=http_path, access_token=token) as conn:
        with conn.cursor() as cur:
            yield cur


def fetchall(sql: str, params: dict | list | None = None) -> list[dict]:
    with cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [_row_to_dict(cols, row) for row in cur.fetchall()]


def fetchone(sql: str, params: dict | list | None = None) -> dict | None:
    with cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        row = cur.fetchone()
        return _row_to_dict(cols, row) if row else None


def _row_to_dict(cols: list[str], row: Any) -> dict:
    out: dict = {}
    for col, value in zip(cols, row):
        out[col] = _normalize(value)
    return out


def _normalize(value: Any) -> Any:
    """Convert Databricks/Decimal/Date/numpy types to JSON-safe Python types."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    cls = value.__class__.__name__
    if cls == "Decimal":
        return float(value)
    # numpy scalars
    if cls.startswith(("int", "float", "bool")) and value.__class__.__module__ == "numpy":
        return value.item()
    # numpy arrays — connector returns ARRAY<…> columns as ndarrays
    if value.__class__.__module__ == "numpy" and cls == "ndarray":
        return [_normalize(v) for v in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    # Row objects (named tuples) returned for STRUCT columns
    if hasattr(value, "asDict"):
        return _normalize(value.asDict())
    return value
