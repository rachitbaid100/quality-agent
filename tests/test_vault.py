from pathlib import Path
import tempfile
import unittest

from quality_agent.vault import Vault, VaultError


class VaultTest(unittest.TestCase):
    def test_sets_and_gets_secret(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(Path(tmpdir) / "secrets.b64")

            vault.set("SERVICE_TOKEN", "test-key")

            self.assertEqual(vault.get("SERVICE_TOKEN"), "test-key")
            self.assertIn("SERVICE_TOKEN", vault.list_keys())

    def test_rejects_empty_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(Path(tmpdir) / "secrets.b64")

            with self.assertRaises(VaultError):
                vault.set("SERVICE_TOKEN", "")

    def test_missing_secret_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(Path(tmpdir) / "secrets.b64")

            self.assertIsNone(vault.get("SERVICE_TOKEN"))


if __name__ == "__main__":
    unittest.main()
