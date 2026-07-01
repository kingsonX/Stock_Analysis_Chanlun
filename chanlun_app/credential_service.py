from __future__ import annotations

from typing import Any

from .system_config_store import SystemConfigStore, mysql_dsn_from_env


class CredentialServiceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CredentialService:
    def __init__(self, store: SystemConfigStore | None = None, dsn: str | None = None):
        self.dsn = str(dsn or mysql_dsn_from_env() or "").strip()
        self.store = store or SystemConfigStore(dsn=self.dsn)

    @property
    def enabled(self) -> bool:
        return bool(self.store.enabled)

    def get_deepseek_config(self) -> dict[str, Any]:
        return {
            "api_key": self._required("DEEPSEEK_API_KEY", "DeepSeek API Key"),
            "base_url": self._optional("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            "model": self._optional("DEEPSEEK_MODEL", "deepseek-v4-pro"),
            "max_tokens": self._safe_int(self._optional("DEEPSEEK_MAX_TOKENS", "5200"), 5200),
            "reasoning_effort": self._optional("DEEPSEEK_REASONING_EFFORT", "high"),
        }

    def get_tushare_token(self) -> str:
        return self._required("TUSHARE_TOKEN", "Tushare Token")

    def get_miaoxiang_config(self) -> dict[str, Any]:
        return {
            "api_key": self._required("MX_APIKEY", "妙想 API Key"),
            "data_base_url": "https://mkapi2.dfcfs.com/finskillshub/api/claw/query",
            "search_base_url": "https://mkapi2.dfcfs.com/finskillshub/api/claw/news-search",
        }

    def _required(self, config_key: str, label: str) -> str:
        if not self.enabled:
            raise CredentialServiceError("未配置 MySQL，题材研究模块暂时无法从数据库读取密钥。", 500)
        value = str(self.store.get_value(config_key) or "").strip()
        if not value:
            raise CredentialServiceError(f"系统配置里缺少 {label}，请先到“系统配置”页面保存并启用。", 500)
        return value

    def _optional(self, config_key: str, default: str) -> str:
        if not self.enabled:
            return default
        value = str(self.store.get_value(config_key) or "").strip()
        return value or default

    @staticmethod
    def _safe_int(raw_value: str, default: int) -> int:
        try:
            return int(str(raw_value or "").strip())
        except ValueError:
            return default
