from __future__ import annotations

import re
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .errors import DatabaseApiError
from .permissions import PluginPermissionService

Identifier = str
Operation = Literal["read", "write"]
CrudAction = Literal["insert", "update", "delete", "select"]

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class DatabaseConnection:
    type: Literal["sqlite"]
    database: str


@dataclass(frozen=True)
class QueryRequest:
    plugin_id: str
    connection: DatabaseConnection
    operation: Operation
    sql: str
    params: dict[str, Any] | None = None


@dataclass(frozen=True)
class CrudRequest:
    plugin_id: str
    connection: DatabaseConnection
    table: str
    action: CrudAction
    data: dict[str, Any] | None = None
    where: dict[str, Any] | None = None
    limit: int = 100


class DatabaseService:
    def __init__(self, permissions: PluginPermissionService) -> None:
        self.permissions = permissions

    def execute_query(self, request: QueryRequest) -> dict[str, object]:
        permission = "database:read" if request.operation == "read" else "database:write"
        self.permissions.require(request.plugin_id, permission)
        if request.operation == "read" and not _looks_like_read_query(request.sql):
            raise DatabaseApiError("read operation only allows SELECT-like SQL")

        start = time.perf_counter()
        with _connect_sqlite(request.connection) as conn:
            try:
                cursor = conn.execute(request.sql, request.params or {})
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    rows = [list(row) for row in cursor.fetchall()]
                else:
                    columns = []
                    rows = []
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": cursor.rowcount if cursor.rowcount >= 0 else len(rows),
                    "duration_ms": round((time.perf_counter() - start) * 1000, 3),
                }
            except sqlite3.Error as exc:
                raise DatabaseApiError(str(exc)) from exc

    def execute_crud(self, request: CrudRequest) -> dict[str, object]:
        permission = "database:read" if request.action == "select" else "database:write"
        self.permissions.require(request.plugin_id, permission)
        _validate_identifier(request.table, "table")
        start = time.perf_counter()

        sql, params = _build_crud_sql(request)
        with _connect_sqlite(request.connection) as conn:
            try:
                cursor = conn.execute(sql, params)
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    rows = [list(row) for row in cursor.fetchall()]
                else:
                    columns = []
                    rows = []
                return {
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": cursor.rowcount if cursor.rowcount >= 0 else len(rows),
                    "duration_ms": round((time.perf_counter() - start) * 1000, 3),
                }
            except sqlite3.Error as exc:
                raise DatabaseApiError(str(exc)) from exc


@contextmanager
def _connect_sqlite(connection: DatabaseConnection) -> Iterator[sqlite3.Connection]:
    if connection.type != "sqlite":
        raise DatabaseApiError("only sqlite connections are supported in the current version")
    database_path = Path(connection.database)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _looks_like_read_query(sql: str) -> bool:
    stripped = sql.strip().lower()
    return stripped.startswith("select") or stripped.startswith("with") or stripped.startswith("pragma")


def _validate_identifier(value: str, label: str) -> None:
    if not _IDENTIFIER_RE.match(value):
        raise DatabaseApiError(f"invalid {label} identifier")


def _build_crud_sql(request: CrudRequest) -> tuple[str, dict[str, Any]]:
    table = request.table
    if request.action == "insert":
        data = _require_data(request.data)
        columns = list(data)
        for column in columns:
            _validate_identifier(column, "column")
        placeholders = [f":data_{column}" for column in columns]
        params = {f"data_{column}": value for column, value in data.items()}
        return (
            f"insert into {table} ({', '.join(columns)}) values ({', '.join(placeholders)})",
            params,
        )

    if request.action == "update":
        data = _require_data(request.data)
        where = _require_where(request.where, request.action)
        assignments = []
        params: dict[str, Any] = {}
        for column, value in data.items():
            _validate_identifier(column, "column")
            assignments.append(f"{column} = :data_{column}")
            params[f"data_{column}"] = value
        where_sql, where_params = _build_where(where)
        params.update(where_params)
        return f"update {table} set {', '.join(assignments)} where {where_sql}", params

    if request.action == "delete":
        where = _require_where(request.where, request.action)
        where_sql, params = _build_where(where)
        return f"delete from {table} where {where_sql}", params

    if request.action == "select":
        where_sql = ""
        params = {}
        if request.where:
            where_sql, params = _build_where(request.where)
            where_sql = f" where {where_sql}"
        limit = max(1, min(request.limit, 1000))
        return f"select * from {table}{where_sql} limit {limit}", params

    raise DatabaseApiError("unsupported CRUD action")


def _require_data(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        raise DatabaseApiError("data is required")
    return data


def _require_where(where: dict[str, Any] | None, action: str) -> dict[str, Any]:
    if not where:
        raise DatabaseApiError(f"where is required for {action}")
    return where


def _build_where(where: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    clauses = []
    params = {}
    for column, value in where.items():
        _validate_identifier(column, "where column")
        key = f"where_{column}"
        clauses.append(f"{column} = :{key}")
        params[key] = value
    return " and ".join(clauses), params
