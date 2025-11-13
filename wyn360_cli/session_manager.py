"""
Session Manager for WYN360-CLI (Phase 4.2.1)

Manages authenticated sessions and cookies for websites.

Features:
- Save/load session cookies
- Session expiration detection
- Session reuse (avoid re-login)
- Automatic cleanup of expired sessions

Storage Structure:
~/.wyn360/
  └── sessions/
      ├── wyn360search_com.session.json
      ├── github_com.session.json
      └── ...
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SessionManager:
    """Manage authenticated sessions and cookies per website."""

    def __init__(self, sessions_dir: Optional[Path] = None):
        """
        Initialize the Session Manager.

        Args:
            sessions_dir: Directory for storing sessions (default: ~/.wyn360/sessions/)
        """
        if sessions_dir is None:
            self.sessions_dir = Path.home() / ".wyn360" / "sessions"
        else:
            self.sessions_dir = Path(sessions_dir)

        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Default session TTL (30 minutes)
        self.default_ttl = 1800

    def _get_session_file(self, domain: str) -> Path:
        """
        Get session file path for a domain.

        Args:
            domain: Website domain (e.g., "wyn360search.com")

        Returns:
            Path to session file
        """
        # Sanitize domain for filename (replace dots with underscores)
        safe_domain = domain.replace(".", "_").replace(":", "_").replace("/", "_")
        return self.sessions_dir / f"{safe_domain}.session.json"

    def save_session(
        self,
        domain: str,
        cookies: List[Dict],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Save session cookies for a domain.

        Args:
            domain: Website domain
            cookies: List of cookie dictionaries from Playwright
            ttl: Time to live in seconds (default: 1800 = 30 minutes)

        Returns:
            True if successful, False otherwise
        """
        try:
            if ttl is None:
                ttl = self.default_ttl

            session_data = {
                "domain": domain,
                "cookies": cookies,
                "created_at": time.time(),
                "expires_at": time.time() + ttl,
                "ttl": ttl
            }

            session_file = self._get_session_file(domain)

            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving session for {domain}: {e}")
            return False

    def get_session(self, domain: str) -> Optional[Dict]:
        """
        Retrieve active session for a domain.

        Args:
            domain: Website domain

        Returns:
            Dictionary with 'cookies', 'created_at', 'expires_at', 'ttl'
            or None if no valid session exists
        """
        try:
            session_file = self._get_session_file(domain)

            if not session_file.exists():
                return None

            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Check if session is expired
            if time.time() > session_data["expires_at"]:
                # Session expired, delete it
                self.clear_session(domain)
                return None

            return session_data

        except Exception as e:
            print(f"Error loading session for {domain}: {e}")
            return None

    def is_session_valid(self, domain: str) -> bool:
        """
        Check if a valid session exists for a domain.

        Args:
            domain: Website domain

        Returns:
            True if valid session exists, False otherwise
        """
        session = self.get_session(domain)
        return session is not None

    def clear_session(self, domain: str) -> bool:
        """
        Delete session for a domain.

        Args:
            domain: Website domain

        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = self._get_session_file(domain)

            if session_file.exists():
                session_file.unlink()
                return True
            else:
                return False

        except Exception as e:
            print(f"Error clearing session for {domain}: {e}")
            return False

    def clear_all_sessions(self) -> bool:
        """
        Delete all stored sessions.

        Returns:
            True if successful, False otherwise
        """
        try:
            for session_file in self.sessions_dir.glob("*.session.json"):
                session_file.unlink()

            return True

        except Exception as e:
            print(f"Error clearing all sessions: {e}")
            return False

    def list_sessions(self) -> List[Dict[str, any]]:
        """
        List all stored sessions with their status.

        Returns:
            List of {domain, is_valid, created_at, expires_at}
        """
        sessions = []

        try:
            for session_file in self.sessions_dir.glob("*.session.json"):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)

                domain = session_data["domain"]
                expires_at = session_data["expires_at"]
                is_valid = time.time() < expires_at

                sessions.append({
                    "domain": domain,
                    "is_valid": is_valid,
                    "created_at": datetime.fromtimestamp(session_data["created_at"]).isoformat(),
                    "expires_at": datetime.fromtimestamp(expires_at).isoformat(),
                    "ttl": session_data["ttl"]
                })

        except Exception as e:
            print(f"Error listing sessions: {e}")

        return sessions

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        removed_count = 0

        try:
            for session_file in self.sessions_dir.glob("*.session.json"):
                with open(session_file, 'r') as f:
                    session_data = json.load(f)

                if time.time() > session_data["expires_at"]:
                    session_file.unlink()
                    removed_count += 1

        except Exception as e:
            print(f"Error cleaning up expired sessions: {e}")

        return removed_count

    def extend_session(self, domain: str, additional_ttl: int = 1800) -> bool:
        """
        Extend the TTL of an existing session.

        Args:
            domain: Website domain
            additional_ttl: Additional time in seconds (default: 1800 = 30 minutes)

        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.get_session(domain)

            if session is None:
                return False

            # Extend expiration time
            session["expires_at"] = time.time() + additional_ttl
            session["ttl"] = additional_ttl

            session_file = self._get_session_file(domain)

            with open(session_file, 'w') as f:
                json.dump(session, f, indent=2)

            return True

        except Exception as e:
            print(f"Error extending session for {domain}: {e}")
            return False
