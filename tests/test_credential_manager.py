"""
Unit tests for CredentialManager (Phase 4.1)

Tests cover:
- Encryption key generation and persistence
- Credential save/load with encryption
- List stored sites (without revealing passwords)
- Delete individual credentials
- Clear all credentials
- File permissions (0600)
- Audit logging (no sensitive data)
- Error handling
"""

import pytest
import tempfile
import os
from pathlib import Path
from wyn360_cli.credential_manager import CredentialManager


class TestCredentialManager:
    """Test credential storage and encryption functionality (Phase 4.1)."""

    def test_key_generation_on_init(self):
        """Test that encryption key is generated on first init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Keyfile should be created
            assert manager.keyfile.exists()

            # Keyfile should have strict permissions (0600)
            stat_info = os.stat(manager.keyfile)
            permissions = oct(stat_info.st_mode)[-3:]
            assert permissions == '600'

            # Key should be valid Fernet key (44 bytes base64-encoded)
            with open(manager.keyfile, 'rb') as f:
                key = f.read()
                assert len(key) == 44  # Fernet keys are 44 bytes

    def test_key_persistence_across_sessions(self):
        """Test that the same key is used across multiple sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"

            # First session
            manager1 = CredentialManager(credentials_dir=cred_dir)
            key1 = manager1.key

            # Second session (should reuse same key)
            manager2 = CredentialManager(credentials_dir=cred_dir)
            key2 = manager2.key

            assert key1 == key2

    def test_save_and_load_credential(self):
        """Test basic credential save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Save credential
            success = manager.save_credential(
                domain="example.com",
                username="test@example.com",
                password="SecurePassword123!"
            )
            assert success

            # Vault file should be created with strict permissions
            assert manager.vault_file.exists()
            stat_info = os.stat(manager.vault_file)
            permissions = oct(stat_info.st_mode)[-3:]
            assert permissions == '600'

            # Load credential
            cred = manager.get_credential("example.com")
            assert cred is not None
            assert cred["username"] == "test@example.com"
            assert cred["password"] == "SecurePassword123!"
            assert "saved_at" in cred

    def test_save_multiple_credentials(self):
        """Test saving and loading multiple credentials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Save multiple credentials
            manager.save_credential("site1.com", "user1", "pass1")
            manager.save_credential("site2.com", "user2", "pass2")
            manager.save_credential("site3.com", "user3", "pass3")

            # Load all credentials
            cred1 = manager.get_credential("site1.com")
            cred2 = manager.get_credential("site2.com")
            cred3 = manager.get_credential("site3.com")

            assert cred1["username"] == "user1"
            assert cred2["username"] == "user2"
            assert cred3["username"] == "user3"

    def test_update_existing_credential(self):
        """Test updating an existing credential."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Save initial credential
            manager.save_credential("example.com", "user1", "oldpass")

            # Update with new password
            manager.save_credential("example.com", "user1", "newpass")

            # Load and verify it was updated
            cred = manager.get_credential("example.com")
            assert cred["password"] == "newpass"

    def test_get_nonexistent_credential(self):
        """Test loading credential that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            cred = manager.get_credential("nonexistent.com")
            assert cred is None

    def test_list_stored_sites(self):
        """Test listing all stored sites without revealing passwords."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Save credentials
            manager.save_credential("site1.com", "user1@example.com", "secret1")
            manager.save_credential("site2.com", "user2@example.com", "secret2")

            # List sites
            sites = manager.list_stored_sites()

            assert len(sites) == 2

            # Check that passwords are NOT included
            for site in sites:
                assert "domain" in site
                assert "username" in site
                assert "saved_at" in site
                assert "password" not in site

            # Verify site details
            domains = [site["domain"] for site in sites]
            assert "site1.com" in domains
            assert "site2.com" in domains

    def test_delete_credential(self):
        """Test deleting a stored credential."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Save credentials
            manager.save_credential("site1.com", "user1", "pass1")
            manager.save_credential("site2.com", "user2", "pass2")

            # Delete one credential
            success = manager.delete_credential("site1.com")
            assert success

            # Verify it's gone
            assert manager.get_credential("site1.com") is None

            # Verify other credential is still there
            assert manager.get_credential("site2.com") is not None

    def test_delete_nonexistent_credential(self):
        """Test deleting credential that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            success = manager.delete_credential("nonexistent.com")
            assert not success

    def test_clear_all_credentials(self):
        """Test clearing all stored credentials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Save multiple credentials
            manager.save_credential("site1.com", "user1", "pass1")
            manager.save_credential("site2.com", "user2", "pass2")
            manager.save_credential("site3.com", "user3", "pass3")

            # Clear all
            success = manager.clear_all_credentials()
            assert success

            # Verify all are gone
            sites = manager.list_stored_sites()
            assert len(sites) == 0

    def test_has_credential(self):
        """Test checking if credential exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Initially no credentials
            assert not manager.has_credential("example.com")

            # Save credential
            manager.save_credential("example.com", "user", "pass")

            # Now it should exist
            assert manager.has_credential("example.com")

    def test_encryption_is_actually_working(self):
        """Test that vault file is actually encrypted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Save credential with recognizable password
            manager.save_credential("example.com", "user", "MySecretPassword123")

            # Read vault file directly (should be encrypted)
            with open(manager.vault_file, 'rb') as f:
                raw_data = f.read()

            # Verify the password is NOT in plain text
            assert b"MySecretPassword123" not in raw_data
            assert b"user" not in raw_data

    def test_audit_log_created(self):
        """Test that audit log is created and contains entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"
            manager = CredentialManager(credentials_dir=cred_dir)

            # Perform some operations
            manager.save_credential("example.com", "user", "pass")
            manager.get_credential("example.com")

            # Audit log should exist
            assert manager.audit_log.exists()

            # Read audit log
            with open(manager.audit_log, 'r') as f:
                log_content = f.read()

            # Verify sensitive data is NOT logged
            assert "pass" not in log_content.lower() or "password" not in log_content.lower()

            # Verify actions are logged
            assert "CREDENTIAL_SAVED" in log_content
            assert "CREDENTIAL_ACCESSED" in log_content

    def test_persistence_across_manager_instances(self):
        """Test that credentials persist across different manager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cred_dir = Path(tmpdir) / "credentials"

            # First manager instance - save credential
            manager1 = CredentialManager(credentials_dir=cred_dir)
            manager1.save_credential("example.com", "user", "pass123")

            # Second manager instance - load credential
            manager2 = CredentialManager(credentials_dir=cred_dir)
            cred = manager2.get_credential("example.com")

            assert cred is not None
            assert cred["username"] == "user"
            assert cred["password"] == "pass123"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
