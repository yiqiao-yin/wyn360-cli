"""
Unit tests for SessionManager (Phase 4.2.1)

Tests cover:
- Save and load session cookies
- Session expiration detection
- Session validity checking
- Clear individual sessions
- Clear all sessions
- List all sessions
- Cleanup expired sessions
- Extend session TTL
"""

import pytest
import tempfile
import time
from pathlib import Path
from wyn360_cli.session_manager import SessionManager


class TestSessionManager:
    """Test session management functionality (Phase 4.2.1)."""

    def test_session_file_creation(self):
        """Test that session file is created with correct naming."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Save session
            cookies = [
                {"name": "session_id", "value": "abc123", "domain": "example.com"}
            ]
            manager.save_session("example.com", cookies)

            # Check file exists with correct name
            session_file = sessions_dir / "example_com.session.json"
            assert session_file.exists()

    def test_save_and_load_session(self):
        """Test basic session save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Create test cookies
            cookies = [
                {"name": "session_id", "value": "test_session_123"},
                {"name": "user_token", "value": "token_456"}
            ]

            # Save session
            success = manager.save_session("example.com", cookies)
            assert success

            # Load session
            session = manager.get_session("example.com")
            assert session is not None
            assert session["domain"] == "example.com"
            assert len(session["cookies"]) == 2
            assert session["cookies"][0]["name"] == "session_id"

    def test_session_with_custom_ttl(self):
        """Test saving session with custom TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            cookies = [{"name": "test", "value": "value"}]

            # Save with 1 hour TTL
            manager.save_session("example.com", cookies, ttl=3600)

            session = manager.get_session("example.com")
            assert session["ttl"] == 3600

    def test_session_expiration(self):
        """Test that expired sessions are not returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            cookies = [{"name": "test", "value": "value"}]

            # Save session with 1 second TTL
            manager.save_session("example.com", cookies, ttl=1)

            # Session should be valid immediately
            assert manager.is_session_valid("example.com")

            # Wait for expiration
            time.sleep(1.5)

            # Session should now be expired
            assert not manager.is_session_valid("example.com")

            # get_session should return None and delete expired session
            session = manager.get_session("example.com")
            assert session is None

            # Session file should be deleted
            session_file = sessions_dir / "example_com.session.json"
            assert not session_file.exists()

    def test_multiple_sessions(self):
        """Test managing multiple sessions for different domains."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Save sessions for multiple domains
            manager.save_session("site1.com", [{"name": "cookie1", "value": "val1"}])
            manager.save_session("site2.com", [{"name": "cookie2", "value": "val2"}])
            manager.save_session("site3.com", [{"name": "cookie3", "value": "val3"}])

            # Verify all sessions exist
            assert manager.is_session_valid("site1.com")
            assert manager.is_session_valid("site2.com")
            assert manager.is_session_valid("site3.com")

            # Load individual sessions
            session1 = manager.get_session("site1.com")
            session2 = manager.get_session("site2.com")

            assert session1["cookies"][0]["name"] == "cookie1"
            assert session2["cookies"][0]["name"] == "cookie2"

    def test_get_nonexistent_session(self):
        """Test loading session that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            session = manager.get_session("nonexistent.com")
            assert session is None

    def test_is_session_valid(self):
        """Test checking session validity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # No session initially
            assert not manager.is_session_valid("example.com")

            # Save session
            manager.save_session("example.com", [{"name": "test", "value": "val"}])

            # Now should be valid
            assert manager.is_session_valid("example.com")

    def test_clear_session(self):
        """Test deleting a single session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Save sessions
            manager.save_session("site1.com", [{"name": "c1", "value": "v1"}])
            manager.save_session("site2.com", [{"name": "c2", "value": "v2"}])

            # Clear one session
            success = manager.clear_session("site1.com")
            assert success

            # Verify it's gone
            assert not manager.is_session_valid("site1.com")

            # Other session should still exist
            assert manager.is_session_valid("site2.com")

    def test_clear_nonexistent_session(self):
        """Test clearing session that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            success = manager.clear_session("nonexistent.com")
            assert not success

    def test_clear_all_sessions(self):
        """Test deleting all sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Save multiple sessions
            manager.save_session("site1.com", [{"name": "c1", "value": "v1"}])
            manager.save_session("site2.com", [{"name": "c2", "value": "v2"}])
            manager.save_session("site3.com", [{"name": "c3", "value": "v3"}])

            # Clear all
            success = manager.clear_all_sessions()
            assert success

            # Verify all are gone
            assert not manager.is_session_valid("site1.com")
            assert not manager.is_session_valid("site2.com")
            assert not manager.is_session_valid("site3.com")

    def test_list_sessions(self):
        """Test listing all sessions with their status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Save sessions
            manager.save_session("site1.com", [{"name": "c1", "value": "v1"}], ttl=3600)
            manager.save_session("site2.com", [{"name": "c2", "value": "v2"}], ttl=1)

            # Wait for one to expire
            time.sleep(1.5)

            # List sessions
            sessions = manager.list_sessions()

            assert len(sessions) == 2

            # Check structure
            for session in sessions:
                assert "domain" in session
                assert "is_valid" in session
                assert "created_at" in session
                assert "expires_at" in session
                assert "ttl" in session

            # One should be valid, one expired
            valid_sessions = [s for s in sessions if s["is_valid"]]
            expired_sessions = [s for s in sessions if not s["is_valid"]]

            assert len(valid_sessions) == 1
            assert len(expired_sessions) == 1

    def test_cleanup_expired_sessions(self):
        """Test automatic cleanup of expired sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Save sessions with different TTLs
            manager.save_session("valid.com", [{"name": "c1", "value": "v1"}], ttl=3600)
            manager.save_session("expired1.com", [{"name": "c2", "value": "v2"}], ttl=1)
            manager.save_session("expired2.com", [{"name": "c3", "value": "v3"}], ttl=1)

            # Wait for some to expire
            time.sleep(1.5)

            # Cleanup
            removed_count = manager.cleanup_expired_sessions()

            assert removed_count == 2

            # Only valid session should remain
            assert manager.is_session_valid("valid.com")
            assert not manager.is_session_valid("expired1.com")
            assert not manager.is_session_valid("expired2.com")

    def test_extend_session(self):
        """Test extending session TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Save session with short TTL
            manager.save_session("example.com", [{"name": "test", "value": "val"}], ttl=2)

            # Get initial expiration time
            session1 = manager.get_session("example.com")
            initial_expires = session1["expires_at"]

            # Wait a bit
            time.sleep(0.5)

            # Extend session
            success = manager.extend_session("example.com", additional_ttl=3600)
            assert success

            # Get new expiration time
            session2 = manager.get_session("example.com")
            new_expires = session2["expires_at"]

            # New expiration should be later than initial
            assert new_expires > initial_expires

    def test_extend_nonexistent_session(self):
        """Test extending session that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            success = manager.extend_session("nonexistent.com")
            assert not success

    def test_session_persistence_across_manager_instances(self):
        """Test that sessions persist across different manager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"

            # First manager - save session
            manager1 = SessionManager(sessions_dir=sessions_dir)
            cookies = [{"name": "session", "value": "test123"}]
            manager1.save_session("example.com", cookies)

            # Second manager - load session
            manager2 = SessionManager(sessions_dir=sessions_dir)
            session = manager2.get_session("example.com")

            assert session is not None
            assert session["cookies"][0]["value"] == "test123"

    def test_domain_name_sanitization(self):
        """Test that domain names are properly sanitized for filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sessions"
            manager = SessionManager(sessions_dir=sessions_dir)

            # Domain with dots and colons
            domain = "https://sub.example.com:8080/path"
            cookies = [{"name": "test", "value": "val"}]

            manager.save_session(domain, cookies)

            # Session should be saved and retrievable
            session = manager.get_session(domain)
            assert session is not None
            assert session["domain"] == domain


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
