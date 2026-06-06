from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from getpass import getpass
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_VAULT_PATH = Path("vault/secrets.b64")
VAULT_VERSION = 1


class VaultError(RuntimeError):
    pass


@dataclass(frozen=True)
class Vault:
    path: Path = DEFAULT_VAULT_PATH

    def get(self, key: str) -> str | None:
        payload = self._read_payload()
        value = payload.get("secrets", {}).get(key)
        return str(value) if value is not None else None

    def set(self, key: str, value: str) -> None:
        if not key.strip():
            raise VaultError("Secret key name cannot be empty.")
        if not value:
            raise VaultError("Secret value cannot be empty.")

        payload = self._read_payload()
        payload.setdefault("version", VAULT_VERSION)
        payload.setdefault("secrets", {})
        payload["secrets"][key.strip()] = value
        self._write_payload(payload)

    def list_keys(self) -> list[str]:
        payload = self._read_payload()
        return sorted(payload.get("secrets", {}).keys())

    def _read_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": VAULT_VERSION, "secrets": {}}

        encoded = "".join(self.path.read_text(encoding="utf-8").split())
        if not encoded:
            return {"version": VAULT_VERSION, "secrets": {}}

        try:
            decoded = base64.b64decode(encoded).decode("utf-8")
            payload = json.loads(decoded)
        except (ValueError, json.JSONDecodeError) as exc:
            raise VaultError(f"Unable to decode vault file: {self.path}") from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("secrets"), dict):
            raise VaultError("Vault payload must contain a secrets object.")

        return payload

    def _write_payload(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        plain_json = json.dumps(payload, indent=2, sort_keys=True)
        encoded = base64.b64encode(plain_json.encode("utf-8")).decode("ascii")
        self.path.write_text(encoded + "\n", encoding="utf-8")


def resolve_secret(key: str, vault_path: Path = DEFAULT_VAULT_PATH) -> str | None:
    return Vault(vault_path).get(key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tcagent-vault",
        description="Manage TC-Agent V1 base64-encoded local secrets.",
    )
    parser.add_argument("--vault-path", type=Path, default=DEFAULT_VAULT_PATH, help="Vault file path.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="Add or update a secret.")
    set_parser.add_argument("key", help="Secret name, for example SERVICE_TOKEN.")
    set_parser.add_argument("--value", help="Secret value. If omitted, a hidden prompt is used.")

    get_parser = subparsers.add_parser("get", help="Print a secret value.")
    get_parser.add_argument("key", help="Secret name.")

    subparsers.add_parser("list", help="List secret names.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    vault = Vault(args.vault_path)

    try:
        if args.command == "set":
            value = args.value or getpass(f"Enter value for {args.key}: ")
            vault.set(args.key, value)
            sys.stdout.write(f"Saved {args.key} to {args.vault_path}\n")
            return 0

        if args.command == "get":
            value = vault.get(args.key)
            if value is None:
                parser.exit(status=1, message=f"Secret not found: {args.key}\n")
            sys.stdout.write(value + "\n")
            return 0

        if args.command == "list":
            keys = vault.list_keys()
            sys.stdout.write("\n".join(keys) + ("\n" if keys else ""))
            return 0
    except VaultError as exc:
        parser.exit(status=2, message=f"Error: {exc}\n")

    parser.exit(status=2, message="Error: unknown vault command.\n")


if __name__ == "__main__":
    raise SystemExit(main())
