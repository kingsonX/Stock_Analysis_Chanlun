import unittest

from chanlun_app.credential_service import CredentialService, CredentialServiceError


class FakeConfigStore:
    def __init__(self, values=None, enabled=True):
        self.values = values or {}
        self.enabled = enabled

    def get_value(self, config_key):
        return self.values.get(str(config_key or "").strip().upper())


class CredentialServiceTest(unittest.TestCase):
    def test_get_deepseek_config_reads_values_from_store(self):
        store = FakeConfigStore(
            values={
                "DEEPSEEK_API_KEY": "sk-demo",
                "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
                "DEEPSEEK_MODEL": "deepseek-v4-pro",
                "DEEPSEEK_MAX_TOKENS": "1800",
                "DEEPSEEK_REASONING_EFFORT": "high",
            }
        )

        service = CredentialService(store=store)

        self.assertEqual(
            service.get_deepseek_config(),
            {
                "api_key": "sk-demo",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-pro",
                "max_tokens": 1800,
                "reasoning_effort": "high",
            },
        )

    def test_get_deepseek_config_uses_defaults_for_optional_values(self):
        store = FakeConfigStore(values={"DEEPSEEK_API_KEY": "sk-demo"})

        service = CredentialService(store=store)

        self.assertEqual(service.get_deepseek_config()["base_url"], "https://api.deepseek.com")
        self.assertEqual(service.get_deepseek_config()["model"], "deepseek-v4-pro")
        self.assertEqual(service.get_deepseek_config()["max_tokens"], 5200)
        self.assertEqual(service.get_deepseek_config()["reasoning_effort"], "high")

    def test_required_raises_when_mysql_store_disabled(self):
        service = CredentialService(store=FakeConfigStore(enabled=False))

        with self.assertRaises(CredentialServiceError) as cm:
            service.get_tushare_token()

        self.assertIn("未配置 MySQL", cm.exception.message)


if __name__ == "__main__":
    unittest.main()
