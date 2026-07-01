from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from .config import BASE_DIR
from .mysql_store import MySQLStoreConnectionError, build_mysql_dsn, mysql_connection


DEFAULT_SYSTEM_CONFIGS: dict[str, dict[str, Any]] = {
    "TUSHARE_TOKEN": {
        "label": "Tushare Token",
        "category": "tushare",
        "description": "Tushare Pro 数据接口密钥。",
        "is_secret": True,
    },
    "MX_APIKEY": {
        "label": "妙想 API Key",
        "category": "eastmoney",
        "description": "东方财富妙想数据接口密钥。",
        "is_secret": True,
    },
    "DEEPSEEK_API_KEY": {
        "label": "DeepSeek API Key",
        "category": "deepseek",
        "description": "DeepSeek 大模型鉴权密钥。",
        "is_secret": True,
    },
    "DEEPSEEK_BASE_URL": {
        "label": "DeepSeek Base URL",
        "category": "deepseek",
        "description": "DeepSeek 兼容接口基础地址。",
        "is_secret": False,
    },
    "DEEPSEEK_MODEL": {
        "label": "DeepSeek 模型",
        "category": "deepseek",
        "description": "默认使用的 DeepSeek 模型名。",
        "is_secret": False,
    },
    "DEEPSEEK_MAX_TOKENS": {
        "label": "DeepSeek Max Tokens",
        "category": "deepseek",
        "description": "DeepSeek 输出 token 上限。",
        "is_secret": False,
    },
    "DEEPSEEK_REASONING_EFFORT": {
        "label": "DeepSeek 推理强度",
        "category": "deepseek",
        "description": "DeepSeek reasoning_effort 配置。",
        "is_secret": False,
    },
    "EASTMONEY_HEADER": {
        "label": "东方财富 Header",
        "category": "eastmoney",
        "description": "东方财富网页版分组接口请求头。",
        "is_secret": True,
    },
    "EASTMONEY_APPKEY": {
        "label": "东方财富 AppKey",
        "category": "eastmoney",
        "description": "东方财富网页版分组接口 appkey。",
        "is_secret": True,
    },
}


_STORE_INSTANCES: dict[str, "SystemConfigStore"] = {}


class SystemConfigStoreError(RuntimeError):
    pass


class SystemConfigStore:
    def __init__(
        self,
        dsn: str | None = None,
        connection_timeout_seconds: float = 2.0,
        cache_ttl_seconds: float = 15.0,
        failure_cooldown_seconds: float = 60.0,
    ):
        self.dsn = str(dsn or "").strip()
        self.connection_timeout_seconds = max(0.2, float(connection_timeout_seconds))
        self.cache_ttl_seconds = max(1.0, float(cache_ttl_seconds))
        self.failure_cooldown_seconds = max(1.0, float(failure_cooldown_seconds))
        self._schema_ready = False
        self._disabled_until = 0.0
        self._value_cache: dict[str, tuple[float, str | None]] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.dsn)

    def list_entries(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    select config_key, label, category, config_value, is_secret, is_enabled, description,
                           created_at, updated_at
                    from system_config_entries
                    order by category asc, config_key asc
                    """
                )
                rows = {
                    _normalize_config_key(row.get("config_key")): _serialize_system_config_row(row, include_value=False)
                    for row in cur.fetchall()
                }
                for config_key, meta in DEFAULT_SYSTEM_CONFIGS.items():
                    rows.setdefault(
                        config_key,
                        {
                            "config_key": config_key,
                            "label": meta.get("label") or config_key,
                            "category": meta.get("category") or "custom",
                            "value_preview": "",
                            "is_secret": bool(meta.get("is_secret", True)),
                            "is_enabled": True,
                            "description": meta.get("description") or "",
                            "created_at": "",
                            "updated_at": "",
                            "source": "preset",
                        },
                    )
                return sorted(rows.values(), key=lambda item: (item.get("category") or "", item.get("config_key") or ""))
        except SystemConfigStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise SystemConfigStoreError(f"读取系统配置失败：{exc}") from exc

    def get_entry(self, config_key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        cleaned_key = _normalize_config_key(config_key)
        if not cleaned_key:
            return None
        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    select config_key, label, category, config_value, is_secret, is_enabled, description,
                           created_at, updated_at
                    from system_config_entries
                    where config_key = %s
                    """,
                    (cleaned_key,),
                )
                row = cur.fetchone()
                if row:
                    return _serialize_system_config_row(row, include_value=True)
                default_meta = DEFAULT_SYSTEM_CONFIGS.get(cleaned_key)
                if not default_meta:
                    return None
                return {
                    "config_key": cleaned_key,
                    "label": default_meta.get("label") or cleaned_key,
                    "category": default_meta.get("category") or "custom",
                    "config_value": "",
                    "value_preview": "",
                    "is_secret": bool(default_meta.get("is_secret", True)),
                    "is_enabled": True,
                    "description": default_meta.get("description") or "",
                    "created_at": "",
                    "updated_at": "",
                    "source": "preset",
                }
        except SystemConfigStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise SystemConfigStoreError(f"读取系统配置详情失败：{exc}") from exc

    def get_value(self, config_key: str) -> str | None:
        if not self.enabled:
            return None
        cleaned_key = _normalize_config_key(config_key)
        if not cleaned_key:
            return None
        cached = self._value_cache.get(cleaned_key)
        now = time.time()
        if cached and cached[0] > now:
            return cached[1]
        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    select config_value
                    from system_config_entries
                    where config_key = %s and is_enabled = 1
                    limit 1
                    """,
                    (cleaned_key,),
                )
                row = cur.fetchone() or {}
                value = str(row.get("config_value") or "").strip() or None
                self._value_cache[cleaned_key] = (now + self.cache_ttl_seconds, value)
                return value
        except SystemConfigStoreError:
            return None
        except Exception:
            self._trip_circuit()
            return None

    def upsert_entry(
        self,
        config_key: str,
        config_value: str,
        label: str = "",
        category: str = "",
        description: str = "",
        is_secret: bool = True,
        is_enabled: bool = True,
    ) -> dict[str, Any]:
        if not self.enabled:
            raise SystemConfigStoreError("未配置 MySQL，暂时无法保存系统配置。")
        cleaned_key = _normalize_config_key(config_key)
        if not cleaned_key:
            raise SystemConfigStoreError("配置键不能为空。")
        default_meta = DEFAULT_SYSTEM_CONFIGS.get(cleaned_key, {})
        resolved_is_secret = bool(default_meta.get("is_secret", is_secret))
        payload = (
            cleaned_key,
            str(label or default_meta.get("label") or cleaned_key).strip(),
            str(category or default_meta.get("category") or "custom").strip().lower() or "custom",
            str(config_value or ""),
            1 if resolved_is_secret else 0,
            1 if is_enabled else 0,
            str(description or default_meta.get("description") or "").strip(),
        )
        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute(
                    """
                    insert into system_config_entries (
                      config_key, label, category, config_value, is_secret, is_enabled, description
                    )
                    values (%s, %s, %s, %s, %s, %s, %s)
                    on duplicate key update
                      label = values(label),
                      category = values(category),
                      config_value = values(config_value),
                      is_secret = values(is_secret),
                      is_enabled = values(is_enabled),
                      description = values(description),
                      updated_at = current_timestamp
                    """,
                    payload,
                )
                self._value_cache.pop(cleaned_key, None)
                cur.execute(
                    """
                    select config_key, label, category, config_value, is_secret, is_enabled, description,
                           created_at, updated_at
                    from system_config_entries
                    where config_key = %s
                    """,
                    (cleaned_key,),
                )
                row = cur.fetchone() or {}
                return _serialize_system_config_row(row, include_value=True)
        except SystemConfigStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise SystemConfigStoreError(f"保存系统配置失败：{exc}") from exc

    def delete_entry(self, config_key: str) -> bool:
        if not self.enabled:
            return False
        cleaned_key = _normalize_config_key(config_key)
        if not cleaned_key:
            return False
        try:
            with self._connection() as conn, conn.cursor() as cur:
                self._ensure_schema(cur)
                cur.execute("delete from system_config_entries where config_key = %s", (cleaned_key,))
                self._value_cache.pop(cleaned_key, None)
                return cur.rowcount > 0
        except SystemConfigStoreError:
            raise
        except Exception as exc:
            self._trip_circuit()
            raise SystemConfigStoreError(f"删除系统配置失败：{exc}") from exc

    def _connection(self):
        if self._disabled_until > time.time():
            raise SystemConfigStoreError("系统配置数据库连接暂时熔断，等待冷却后再试。")
        try:
            return mysql_connection(self.dsn, connect_timeout_seconds=self.connection_timeout_seconds)
        except MySQLStoreConnectionError as exc:
            raise SystemConfigStoreError(str(exc)) from exc

    def _ensure_schema(self, cur) -> None:
        if self._schema_ready:
            return
        cur.execute(
            """
            create table if not exists system_config_entries (
              config_key varchar(64) not null primary key,
              label varchar(64) not null default '',
              category varchar(32) not null default 'custom',
              config_value longtext not null,
              is_secret tinyint(1) not null default 1,
              is_enabled tinyint(1) not null default 1,
              description varchar(255) not null default '',
              created_at datetime not null default current_timestamp,
              updated_at datetime not null default current_timestamp on update current_timestamp,
              key idx_system_config_category (category),
              key idx_system_config_enabled (is_enabled),
              key idx_system_config_updated_at (updated_at)
            ) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci
            """
        )
        self._seed_defaults_from_env(cur)
        self._schema_ready = True

    def _trip_circuit(self) -> None:
        self._schema_ready = False
        self._disabled_until = time.time() + self.failure_cooldown_seconds

    def _seed_defaults_from_env(self, cur) -> None:
        for config_key, meta in DEFAULT_SYSTEM_CONFIGS.items():
            env_value = raw_env_value(config_key)
            if env_value in (None, ""):
                continue
            cur.execute("select 1 from system_config_entries where config_key = %s limit 1", (config_key,))
            if cur.fetchone():
                continue
            cur.execute(
                """
                insert into system_config_entries (
                  config_key, label, category, config_value, is_secret, is_enabled, description
                )
                values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    config_key,
                    str(meta.get("label") or config_key),
                    str(meta.get("category") or "custom"),
                    str(env_value),
                    1 if bool(meta.get("is_secret", True)) else 0,
                    1,
                    str(meta.get("description") or ""),
                ),
            )


def get_system_config_store(dsn: str | None = None) -> SystemConfigStore:
    cleaned_dsn = str(dsn or mysql_dsn_from_env() or "").strip()
    if cleaned_dsn not in _STORE_INSTANCES:
        _STORE_INSTANCES[cleaned_dsn] = SystemConfigStore(dsn=cleaned_dsn)
    return _STORE_INSTANCES[cleaned_dsn]


def managed_config_value(name: str, default: str | None = None, dsn: str | None = None) -> str | None:
    cleaned_name = _normalize_config_key(name)
    if not cleaned_name:
        return default
    store = get_system_config_store(dsn)
    value = store.get_value(cleaned_name) if store.enabled else None
    if value not in (None, ""):
        return value
    return raw_env_value(cleaned_name) or default


def raw_env_value(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value

    env_file = Path(BASE_DIR) / ".env"
    if not env_file.exists():
        return None

    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        if key.strip() == name:
            return raw_value.strip().strip('"').strip("'")
    return None


def safe_env_int(name: str, default: int) -> int:
    raw = raw_env_value(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def mysql_dsn_from_env() -> str:
    explicit = raw_env_value("MYSQL_URL")
    if explicit:
        return explicit

    database_url = raw_env_value("DATABASE_URL")
    if database_url and database_url.lower().startswith("mysql"):
        return database_url

    host = raw_env_value("MYSQL_HOST")
    user = raw_env_value("MYSQL_USER")
    database = raw_env_value("MYSQL_DATABASE")
    if not (host and user and database):
        return ""

    port = safe_env_int("MYSQL_PORT", 3306)
    password = raw_env_value("MYSQL_PASSWORD") or ""
    charset = raw_env_value("MYSQL_CHARSET") or "utf8mb4"
    return build_mysql_dsn(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset=charset,
    )


def _normalize_config_key(value: Any) -> str:
    return str(value or "").strip().upper()


def _serialize_system_config_row(row: dict[str, Any], include_value: bool) -> dict[str, Any]:
    config_key = _normalize_config_key(row.get("config_key"))
    config_value = str(row.get("config_value") or "")
    is_secret = bool(int(row.get("is_secret") or 0))
    value_preview = _masked_preview(config_value, is_secret=is_secret)
    payload = {
        "config_key": config_key,
        "label": str(row.get("label") or config_key).strip(),
        "category": str(row.get("category") or "custom").strip().lower() or "custom",
        "value_preview": value_preview,
        "is_secret": is_secret,
        "is_enabled": bool(int(row.get("is_enabled") or 0)),
        "description": str(row.get("description") or "").strip(),
        "created_at": _stringify_datetime(row.get("created_at")),
        "updated_at": _stringify_datetime(row.get("updated_at")),
        "source": "mysql",
    }
    if include_value:
        payload["config_value"] = config_value
    return payload


def _masked_preview(value: str, is_secret: bool) -> str:
    text = str(value or "")
    if not text:
        return ""
    if not is_secret:
        return text[:96]
    if len(text) <= 8:
        return "*" * len(text)
    return f"{text[:4]}{'*' * min(12, len(text) - 8)}{text[-4:]}"


def _stringify_datetime(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value)
