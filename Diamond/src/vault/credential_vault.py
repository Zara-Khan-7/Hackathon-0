"""Credential Vault — secure storage for API keys, tokens, and secrets.

Mock implementation uses an in-memory dict with base64 encoding.
Production would use Fernet symmetric encryption (cryptography library).
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any


class CredentialVault:
    """Mock encrypted credential vault.

    In production, this uses Fernet encryption from the cryptography library.
    Mock mode stores credentials as base64-encoded JSON (NOT secure, demo only).
    """

    def __init__(self, vault_path: str | Path | None = None, mock: bool = True):
        self._mock = mock
        self._vault_path = Path(vault_path) if vault_path else None
        self._store: dict[str, dict] = {}
        self._access_log: list[dict] = []

        if self._vault_path and self._vault_path.exists():
            self._load()

    def store(self, key: str, value: str, metadata: dict | None = None) -> None:
        """Store a credential in the vault."""
        self._store[key] = {
            "value": self._encode(value),
            "metadata": metadata or {},
            "stored_at": time.time(),
            "accessed_at": None,
        }
        self._log_access(key, "store")
        self._persist()

    def retrieve(self, key: str) -> str | None:
        """Retrieve a credential from the vault."""
        entry = self._store.get(key)
        if entry is None:
            self._log_access(key, "retrieve_miss")
            return None

        entry["accessed_at"] = time.time()
        self._log_access(key, "retrieve")
        return self._decode(entry["value"])

    def delete(self, key: str) -> bool:
        """Delete a credential from the vault."""
        if key in self._store:
            del self._store[key]
            self._log_access(key, "delete")
            self._persist()
            return True
        return False

    def list_keys(self) -> list[str]:
        """List all stored credential keys (not values)."""
        return list(self._store.keys())

    def has(self, key: str) -> bool:
        """Check if a credential exists."""
        return key in self._store

    def get_metadata(self, key: str) -> dict | None:
        """Get metadata for a credential without accessing the value."""
        entry = self._store.get(key)
        if entry is None:
            return None
        return {
            "key": key,
            "metadata": entry["metadata"],
            "stored_at": entry["stored_at"],
            "accessed_at": entry["accessed_at"],
        }

    def _encode(self, value: str) -> str:
        """Encode a value (mock: base64, production: Fernet encrypt)."""
        if self._mock:
            return base64.b64encode(value.encode()).decode()
        # Production would use:
        # from cryptography.fernet import Fernet
        # return Fernet(key).encrypt(value.encode()).decode()
        return base64.b64encode(value.encode()).decode()

    def _decode(self, encoded: str) -> str:
        """Decode a value (mock: base64, production: Fernet decrypt)."""
        if self._mock:
            return base64.b64decode(encoded.encode()).decode()
        return base64.b64decode(encoded.encode()).decode()

    def _persist(self) -> None:
        """Save vault to disk."""
        if self._vault_path is None:
            return
        self._vault_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(self._store, indent=2)
        encoded = base64.b64encode(data.encode()).decode()
        with open(self._vault_path, "w", encoding="utf-8") as f:
            f.write(encoded)

    def _load(self) -> None:
        """Load vault from disk."""
        if self._vault_path is None or not self._vault_path.exists():
            return
        try:
            with open(self._vault_path, "r", encoding="utf-8") as f:
                encoded = f.read()
            data = base64.b64decode(encoded.encode()).decode()
            self._store = json.loads(data)
        except Exception:
            self._store = {}

    def _log_access(self, key: str, action: str) -> None:
        """Log vault access for audit trail."""
        self._access_log.append({
            "key": key,
            "action": action,
            "timestamp": time.time(),
        })

    def get_access_log(self, last_n: int | None = None) -> list[dict]:
        """Get vault access log."""
        if last_n:
            return self._access_log[-last_n:]
        return list(self._access_log)

    def get_stats(self) -> dict:
        return {
            "total_credentials": len(self._store),
            "mock_mode": self._mock,
            "access_log_entries": len(self._access_log),
            "persisted": self._vault_path is not None,
        }
