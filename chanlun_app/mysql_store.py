from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse


_READY_DATABASES: set[tuple[str, int, str, str]] = set()


class MySQLStoreConnectionError(RuntimeError):
    pass


def parse_mysql_dsn(dsn: str) -> dict[str, Any]:
    text = str(dsn or "").strip()
    if not text:
        return {}
    parsed = urlparse(text)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise MySQLStoreConnectionError("数据库连接串必须使用 mysql:// 或 mysql+pymysql://。")
    database = parsed.path.lstrip("/")
    if not database:
        raise MySQLStoreConnectionError("MySQL 连接串缺少数据库名。")
    query = parse_qs(parsed.query or "")
    charset = (query.get("charset") or ["utf8mb4"])[0] or "utf8mb4"
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": int(parsed.port or 3306),
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": database,
        "charset": charset,
    }


def build_mysql_dsn(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    charset: str = "utf8mb4",
) -> str:
    safe_user = quote(str(user or ""), safe="")
    safe_password = quote(str(password or ""), safe="")
    safe_database = quote(str(database or ""), safe="")
    return f"mysql://{safe_user}:{safe_password}@{host}:{int(port)}/{safe_database}?charset={charset}"


def mysql_enabled(dsn: str | None) -> bool:
    return bool(str(dsn or "").strip())


def mysql_error_prefix(label: str, exc: Exception) -> str:
    return f"{label}：{exc}"


@contextmanager
def mysql_connection(dsn: str, connect_timeout_seconds: float = 2.0):
    connect_kwargs = _connect_kwargs(dsn, connect_timeout_seconds)
    _ensure_database(connect_kwargs)
    connection = _open_connection(connect_kwargs, include_database=True)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _connect_kwargs(dsn: str, connect_timeout_seconds: float) -> dict[str, Any]:
    config = parse_mysql_dsn(dsn)
    if not config:
        raise MySQLStoreConnectionError("未配置 MYSQL_URL，无法连接 MySQL。")
    config["connect_timeout"] = max(1, int(round(connect_timeout_seconds)))
    return config


def _ensure_database(connect_kwargs: dict[str, Any]) -> None:
    key = (
        str(connect_kwargs.get("host") or ""),
        int(connect_kwargs.get("port") or 3306),
        str(connect_kwargs.get("user") or ""),
        str(connect_kwargs.get("database") or ""),
    )
    if key in _READY_DATABASES:
        return
    connection = _open_connection(connect_kwargs, include_database=False)
    try:
        with connection.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{connect_kwargs['database']}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
        _READY_DATABASES.add(key)
    finally:
        connection.close()


def _open_connection(connect_kwargs: dict[str, Any], include_database: bool):
    try:
        import pymysql
    except Exception as exc:
        raise MySQLStoreConnectionError("未安装 PyMySQL，无法启用 MySQL 缓存。") from exc

    kwargs = {
        "host": connect_kwargs["host"],
        "port": connect_kwargs["port"],
        "user": connect_kwargs["user"],
        "password": connect_kwargs["password"],
        "charset": connect_kwargs.get("charset") or "utf8mb4",
        "connect_timeout": connect_kwargs.get("connect_timeout", 2),
        "autocommit": False,
        "cursorclass": pymysql.cursors.DictCursor,
    }
    if include_database:
        kwargs["database"] = connect_kwargs["database"]
    return pymysql.connect(**kwargs)
