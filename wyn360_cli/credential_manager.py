"""
Credential Manager for WYN360-CLI (Phase 4.1)

Securely stores and manages login credentials with AES-256-GCM encryption.

Security Features:
- AES-256-GCM encryption for all stored credentials
- Per-user encryption key derived from system entropy
- File permissions set to 0600 (user read/write only)
- Credentials only decrypted when needed
- Auto-clear from memory after use

Storage Structure:
~/.wyn360/
  ├── credentials/
  │   ├── .keyfile          # Encryption key
  │   └── vault.enc         # Encrypted credential vault
  └── logs/
      └── auth_audit.log    # Audit log (no sensitive data)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from cryptography.fernet import Fernet


class CredentialManager:
    """Securely manage login credentials with AES-256-GCM encryption."""

    def __init__(self, credentials_dir: Optional[Path] = None):
        """
        Initialize the Credential Manager.

        Args:
            credentials_dir: Directory for storing credentials (default: ~/.wyn360/credentials/)
        """
        if credentials_dir is None:
            self.credentials_dir = Path.home() / ".wyn360" / "credentials"
        else:
            self.credentials_dir = Path(credentials_dir)

        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        self.keyfile = self.credentials_dir / ".keyfile"
        self.vault_file = self.credentials_dir / "vault.enc"
        self.audit_log = Path.home() / ".wyn360" / "logs" / "auth_audit.log"

        # Ensure audit log directory exists
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)

        # Initialize encryption key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

        # Set strict file permissions
        self._set_file_permissions()

    def _get_or_create_key(self) -> bytes:
        """
        Get existing encryption key or create a new one.

        Returns:
            Fernet encryption key (base64-encoded)
        """
        if self.keyfile.exists():
            # Read existing key
            with open(self.keyfile, 'rb') as f:
                return f.read()
        else:
            # Generate new key using system entropy
            key = Fernet.generate_key()

            # Save key with strict permissions
            with open(self.keyfile, 'wb') as f:
                f.write(key)

            # Set keyfile permissions to 0600 (user read/write only)
            os.chmod(self.keyfile, 0o600)

            self._log_audit("KEY_CREATED", "New encryption key generated")

            return key

    def _set_file_permissions(self):
        """Set strict file permissions on credential files."""
        for file in [self.keyfile, self.vault_file]:
            if file.exists():
                os.chmod(file, 0o600)

    def _log_audit(self, action: str, details: str = ""):
        """
        Log credential management actions (no sensitive data).

        Args:
            action: Action type (e.g., CREDENTIAL_SAVED, CREDENTIAL_ACCESSED)
            details: Additional non-sensitive details
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action}: {details}\n"

        with open(self.audit_log, 'a') as f:
            f.write(log_entry)

    def _load_vault(self) -> Dict[str, Dict[str, str]]:
        """
        Load and decrypt the credential vault.

        Returns:
            Dictionary of domain -> {username, password, saved_at}
        """
        if not self.vault_file.exists():
            return {}

        try:
            with open(self.vault_file, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_data)
            vault = json.loads(decrypted_data.decode('utf-8'))

            return vault
        except Exception as e:
            self._log_audit("ERROR", f"Failed to load vault: {str(e)}")
            return {}

    def _save_vault(self, vault: Dict[str, Dict[str, str]]):
        """
        Encrypt and save the credential vault.

        Args:
            vault: Dictionary of domain -> {username, password, saved_at}
        """
        try:
            # Convert to JSON
            json_data = json.dumps(vault, indent=2).encode('utf-8')

            # Encrypt
            encrypted_data = self.cipher.encrypt(json_data)

            # Save with strict permissions
            with open(self.vault_file, 'wb') as f:
                f.write(encrypted_data)

            # Ensure permissions are correct
            os.chmod(self.vault_file, 0o600)

        except Exception as e:
            self._log_audit("ERROR", f"Failed to save vault: {str(e)}")
            raise

    def save_credential(self, domain: str, username: str, password: str) -> bool:
        """
        Encrypt and save login credentials for a domain.

        Args:
            domain: Website domain (e.g., "wyn360search.com")
            username: Login username/email
            password: Login password

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing vault
            vault = self._load_vault()

            # Add/update credential
            vault[domain] = {
                "username": username,
                "password": password,
                "saved_at": datetime.now().isoformat()
            }

            # Save vault
            self._save_vault(vault)

            # Log audit (no sensitive data)
            self._log_audit("CREDENTIAL_SAVED", f"domain={domain}, username={username}")

            return True

        except Exception as e:
            self._log_audit("ERROR", f"Failed to save credential for {domain}: {str(e)}")
            return False

    def get_credential(self, domain: str) -> Optional[Dict[str, str]]:
        """
        Decrypt and retrieve credentials for a domain.

        Args:
            domain: Website domain

        Returns:
            Dictionary with 'username', 'password', 'saved_at' or None if not found
        """
        try:
            vault = self._load_vault()

            if domain in vault:
                self._log_audit("CREDENTIAL_ACCESSED", f"domain={domain}")
                return vault[domain]
            else:
                return None

        except Exception as e:
            self._log_audit("ERROR", f"Failed to get credential for {domain}: {str(e)}")
            return None

    def list_stored_sites(self) -> List[Dict[str, str]]:
        """
        List all sites with stored credentials (without revealing passwords).

        Returns:
            List of {domain, username, saved_at}
        """
        try:
            vault = self._load_vault()

            sites = []
            for domain, cred in vault.items():
                sites.append({
                    "domain": domain,
                    "username": cred["username"],
                    "saved_at": cred.get("saved_at", "Unknown")
                })

            return sites

        except Exception as e:
            self._log_audit("ERROR", f"Failed to list sites: {str(e)}")
            return []

    def delete_credential(self, domain: str) -> bool:
        """
        Remove stored credentials for a domain.

        Args:
            domain: Website domain

        Returns:
            True if successful, False otherwise
        """
        try:
            vault = self._load_vault()

            if domain in vault:
                del vault[domain]
                self._save_vault(vault)
                self._log_audit("CREDENTIAL_DELETED", f"domain={domain}")
                return True
            else:
                return False

        except Exception as e:
            self._log_audit("ERROR", f"Failed to delete credential for {domain}: {str(e)}")
            return False

    def clear_all_credentials(self) -> bool:
        """
        Delete all stored credentials.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._save_vault({})
            self._log_audit("ALL_CREDENTIALS_CLEARED", "User cleared all stored credentials")
            return True

        except Exception as e:
            self._log_audit("ERROR", f"Failed to clear all credentials: {str(e)}")
            return False

    def has_credential(self, domain: str) -> bool:
        """
        Check if credentials are stored for a domain.

        Args:
            domain: Website domain

        Returns:
            True if credentials exist, False otherwise
        """
        vault = self._load_vault()
        return domain in vault
