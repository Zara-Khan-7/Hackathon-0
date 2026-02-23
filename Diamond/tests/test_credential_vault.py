"""Tests for credential vault."""

import pytest
from src.vault.credential_vault import CredentialVault


class TestCredentialVault:
    def test_store_and_retrieve(self):
        vault = CredentialVault()
        vault.store("api_key", "sk-12345")
        assert vault.retrieve("api_key") == "sk-12345"

    def test_retrieve_nonexistent(self):
        vault = CredentialVault()
        assert vault.retrieve("nonexistent") is None

    def test_delete(self):
        vault = CredentialVault()
        vault.store("api_key", "sk-12345")
        assert vault.delete("api_key") is True
        assert vault.retrieve("api_key") is None

    def test_delete_nonexistent(self):
        vault = CredentialVault()
        assert vault.delete("nonexistent") is False

    def test_list_keys(self):
        vault = CredentialVault()
        vault.store("key1", "val1")
        vault.store("key2", "val2")
        keys = vault.list_keys()
        assert "key1" in keys
        assert "key2" in keys

    def test_has(self):
        vault = CredentialVault()
        vault.store("key1", "val1")
        assert vault.has("key1") is True
        assert vault.has("key2") is False

    def test_metadata(self):
        vault = CredentialVault()
        vault.store("key1", "val1", metadata={"env": "prod"})
        meta = vault.get_metadata("key1")
        assert meta is not None
        assert meta["metadata"]["env"] == "prod"

    def test_persist_and_reload(self, tmp_path):
        vault_path = tmp_path / "vault.enc"
        vault1 = CredentialVault(vault_path=vault_path)
        vault1.store("api_key", "sk-12345")

        vault2 = CredentialVault(vault_path=vault_path)
        assert vault2.retrieve("api_key") == "sk-12345"

    def test_access_log(self):
        vault = CredentialVault()
        vault.store("key1", "val1")
        vault.retrieve("key1")
        log = vault.get_access_log()
        assert len(log) == 2  # store + retrieve
        assert log[0]["action"] == "store"
        assert log[1]["action"] == "retrieve"

    def test_access_log_miss(self):
        vault = CredentialVault()
        vault.retrieve("missing")
        log = vault.get_access_log()
        assert log[0]["action"] == "retrieve_miss"

    def test_stats(self):
        vault = CredentialVault()
        vault.store("key1", "val1")
        stats = vault.get_stats()
        assert stats["total_credentials"] == 1
        assert stats["mock_mode"] is True

    def test_encoding_roundtrip(self):
        vault = CredentialVault()
        special_value = "p@$$w0rd!#%^&*()"
        vault.store("special", special_value)
        assert vault.retrieve("special") == special_value
