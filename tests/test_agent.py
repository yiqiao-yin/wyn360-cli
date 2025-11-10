"""Unit tests for agent.py"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from wyn360_cli.agent import WYN360Agent


class TestWYN360Agent:
    """Tests for WYN360Agent class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = Path.cwd()
        # Change to test directory
        import os
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up after tests"""
        import os
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_agent_initialization(self):
        """Test that agent initializes correctly"""
        agent = WYN360Agent(api_key="test_key", model="claude-sonnet-4-20250514")
        assert agent.api_key == "test_key"
        assert agent.model_name == "claude-sonnet-4-20250514"
        assert agent.conversation_history == []

    def test_system_prompt_contains_key_instructions(self):
        """Test that system prompt has necessary instructions"""
        agent = WYN360Agent(api_key="test_key")
        prompt = agent._get_system_prompt()
        assert "WYN360" in prompt
        assert "coding assistant" in prompt.lower()
        assert "python" in prompt.lower()
        # Check for file operation intelligence
        assert "overwrite=True" in prompt
        assert "read_file first" in prompt.lower()

    @pytest.mark.asyncio
    async def test_read_file_tool(self):
        """Test the read_file tool"""
        # Create a test file
        test_file = Path(self.test_dir) / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        agent = WYN360Agent(api_key="test_key")
        result = await agent.read_file(None, str(test_file))

        assert test_content in result
        assert "test.txt" in result

    @pytest.mark.asyncio
    async def test_read_file_tool_nonexistent(self):
        """Test read_file with nonexistent file"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.read_file(None, "nonexistent.txt")

        assert "Error" in result
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_write_file_tool(self):
        """Test the write_file tool"""
        agent = WYN360Agent(api_key="test_key")
        file_path = str(Path(self.test_dir) / "new_file.txt")
        content = "Test content"

        result = await agent.write_file(None, file_path, content, overwrite=False)

        assert "Successfully" in result or "wrote" in result.lower()
        assert Path(file_path).exists()
        assert Path(file_path).read_text() == content

    @pytest.mark.asyncio
    async def test_write_file_tool_no_overwrite(self):
        """Test write_file doesn't overwrite by default"""
        # Create existing file
        test_file = Path(self.test_dir) / "existing.txt"
        test_file.write_text("Original")

        agent = WYN360Agent(api_key="test_key")
        result = await agent.write_file(None, str(test_file), "New", overwrite=False)

        assert "already exists" in result.lower()
        assert test_file.read_text() == "Original"

    @pytest.mark.asyncio
    async def test_list_files_tool(self):
        """Test the list_files tool"""
        # Create some test files
        (Path(self.test_dir) / "test.py").write_text("code")
        (Path(self.test_dir) / "readme.md").write_text("docs")

        agent = WYN360Agent(api_key="test_key")
        result = await agent.list_files(None, self.test_dir)

        assert "test.py" in result
        assert "readme.md" in result

    @pytest.mark.asyncio
    async def test_list_files_empty_directory(self):
        """Test list_files on empty directory"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.list_files(None, self.test_dir)

        assert "No files found" in result

    @pytest.mark.asyncio
    async def test_get_project_info_tool(self):
        """Test the get_project_info tool"""
        # Create a test file
        (Path(self.test_dir) / "test.py").write_text("code")

        agent = WYN360Agent(api_key="test_key")
        result = await agent.get_project_info(None)

        assert "Project Summary" in result
        assert "test.py" in result

    @pytest.mark.asyncio
    async def test_get_project_info_blank_project(self):
        """Test get_project_info on blank project"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.get_project_info(None)

        assert "blank" in result.lower() or "new" in result.lower()

    def test_suggest_filename_streamlit(self):
        """Test filename suggestion for streamlit code"""
        agent = WYN360Agent(api_key="test_key")
        code = "import streamlit as st\nst.write('Hello')"
        filename = agent._suggest_filename(code)

        assert filename == "app.py"

    def test_suggest_filename_main(self):
        """Test filename suggestion for main function"""
        agent = WYN360Agent(api_key="test_key")
        code = "def main():\n    print('hello')"
        filename = agent._suggest_filename(code)

        assert filename == "main.py"

    def test_suggest_filename_class(self):
        """Test filename suggestion for class"""
        agent = WYN360Agent(api_key="test_key")
        code = "class MyClass:\n    pass"
        filename = agent._suggest_filename(code)

        assert filename in ["main.py", "script.py"]

    def test_suggest_filename_default(self):
        """Test default filename suggestion"""
        agent = WYN360Agent(api_key="test_key")
        code = "x = 1 + 2"
        filename = agent._suggest_filename(code)

        assert filename == "script.py"

    @pytest.mark.asyncio
    async def test_chat_updates_history(self, mocker):
        """Test that chat updates conversation history"""
        agent = WYN360Agent(api_key="test_key")

        # Mock the agent.run method
        mock_result = Mock()
        mock_result.data = None  # Set data to None so it falls back to output
        mock_result.output = "Test response"
        mocker.patch.object(agent.agent, 'run', return_value=mock_result)

        initial_length = len(agent.conversation_history)
        await agent.chat("Hello")

        # Should add both user and assistant messages
        assert len(agent.conversation_history) == initial_length + 2
        assert agent.conversation_history[-2]['role'] == 'user'
        assert agent.conversation_history[-1]['role'] == 'assistant'

    @pytest.mark.asyncio
    async def test_chat_handles_errors(self, mocker):
        """Test that chat handles errors gracefully"""
        agent = WYN360Agent(api_key="test_key")

        # Mock the agent.run to raise an exception
        mocker.patch.object(agent.agent, 'run', side_effect=Exception("Test error"))

        response = await agent.chat("Hello")

        assert "error" in response.lower()
        assert "Test error" in response


class TestHistoryManagement:
    """Tests for conversation history management"""

    def test_initialization_with_history(self):
        """Test that agent initializes with history enabled by default"""
        agent = WYN360Agent(api_key="test_key", use_history=True)
        assert agent.use_history is True
        assert agent.conversation_history == []
        assert agent.total_input_tokens == 0
        assert agent.total_output_tokens == 0
        assert agent.request_count == 0

    def test_initialization_without_history(self):
        """Test that agent can be initialized with history disabled"""
        agent = WYN360Agent(api_key="test_key", use_history=False)
        assert agent.use_history is False
        assert agent.conversation_history == []

    def test_clear_history(self):
        """Test clearing conversation history"""
        agent = WYN360Agent(api_key="test_key")
        # Manually add some history
        agent.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        agent.total_input_tokens = 100
        agent.total_output_tokens = 50
        agent.request_count = 1

        agent.clear_history()

        assert agent.conversation_history == []
        assert agent.total_input_tokens == 0
        assert agent.total_output_tokens == 0
        assert agent.request_count == 0
        assert agent.token_history == []

    def test_get_history(self):
        """Test getting conversation history"""
        agent = WYN360Agent(api_key="test_key")
        agent.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]

        history = agent.get_history()

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        # Should return a copy
        assert history is not agent.conversation_history

    def test_save_session(self):
        """Test saving session to JSON file"""
        import tempfile
        agent = WYN360Agent(api_key="test_key", model="claude-sonnet-4-20250514")
        agent.conversation_history = [
            {"role": "user", "content": "Test message"}
        ]
        agent.total_input_tokens = 100
        agent.total_output_tokens = 50
        agent.request_count = 1

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/test_session.json"
            success = agent.save_session(filepath)

            assert success is True
            assert Path(filepath).exists()

            # Verify JSON content
            import json
            with open(filepath, 'r') as f:
                data = json.load(f)

            assert data["model"] == "claude-sonnet-4-20250514"
            assert len(data["conversation_history"]) == 1
            assert data["total_input_tokens"] == 100
            assert data["total_output_tokens"] == 50
            assert data["request_count"] == 1

    def test_save_session_creates_directories(self):
        """Test that save_session creates parent directories"""
        import tempfile
        agent = WYN360Agent(api_key="test_key")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/nested/path/session.json"
            success = agent.save_session(filepath)

            assert success is True
            assert Path(filepath).exists()

    def test_load_session(self):
        """Test loading session from JSON file"""
        import tempfile
        import json

        agent = WYN360Agent(api_key="test_key")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/test_session.json"

            # Create a test session file
            session_data = {
                "model": "claude-sonnet-4-20250514",
                "conversation_history": [
                    {"role": "user", "content": "Test"}
                ],
                "total_input_tokens": 200,
                "total_output_tokens": 100,
                "request_count": 2,
                "token_history": [{"request_number": 1}],
                "timestamp": "2025-01-01"
            }

            with open(filepath, 'w') as f:
                json.dump(session_data, f)

            # Load the session
            success = agent.load_session(filepath)

            assert success is True
            assert len(agent.conversation_history) == 1
            assert agent.total_input_tokens == 200
            assert agent.total_output_tokens == 100
            assert agent.request_count == 2
            assert len(agent.token_history) == 1

    def test_load_session_nonexistent_file(self):
        """Test loading from nonexistent file"""
        agent = WYN360Agent(api_key="test_key")
        success = agent.load_session("/nonexistent/session.json")

        assert success is False

    def test_get_token_stats(self):
        """Test getting token usage statistics"""
        agent = WYN360Agent(api_key="test_key")
        agent.total_input_tokens = 1_000_000  # 1M tokens
        agent.total_output_tokens = 500_000   # 500K tokens
        agent.request_count = 10

        stats = agent.get_token_stats()

        assert stats["total_requests"] == 10
        assert stats["total_input_tokens"] == 1_000_000
        assert stats["total_output_tokens"] == 500_000
        assert stats["total_tokens"] == 1_500_000

        # Cost calculations
        # Input: 1M tokens * $3 per M = $3
        # Output: 500K tokens * $15 per M = $7.50
        # Total: $10.50
        assert stats["input_cost"] == 3.0
        assert stats["output_cost"] == 7.5
        assert stats["total_cost"] == 10.5
        assert stats["avg_cost_per_request"] == 1.05

    def test_get_token_stats_no_requests(self):
        """Test token stats with no requests"""
        agent = WYN360Agent(api_key="test_key")
        stats = agent.get_token_stats()

        assert stats["total_requests"] == 0
        assert stats["total_cost"] == 0.0
        assert stats["avg_cost_per_request"] == 0.0

    def test_estimate_tokens(self):
        """Test token estimation"""
        agent = WYN360Agent(api_key="test_key")

        # Test with empty string
        assert agent._estimate_tokens("") == 0

        # Test with typical text (1 token ≈ 4 characters)
        text = "Hello, World!"  # 13 characters
        assert agent._estimate_tokens(text) == 3  # 13 // 4 = 3

        # Test with longer text
        text = "a" * 400  # 400 characters
        assert agent._estimate_tokens(text) == 100  # 400 // 4 = 100

    @pytest.mark.asyncio
    async def test_track_tokens(self, mocker):
        """Test token tracking during chat"""
        agent = WYN360Agent(api_key="test_key")

        # Mock the agent.run method
        mock_result = Mock()
        mock_result.data = None  # Set data to None so it falls back to output
        mock_result.output = "Short response"
        mocker.patch.object(agent.agent, 'run', return_value=mock_result)

        initial_tokens = agent.total_input_tokens
        initial_requests = agent.request_count

        await agent.chat("Hello")

        # Should have tracked tokens
        assert agent.total_input_tokens > initial_tokens
        assert agent.total_output_tokens > 0
        assert agent.request_count == initial_requests + 1
        assert len(agent.token_history) == 1

        # Check token history entry
        entry = agent.token_history[0]
        assert entry["request_number"] == 1
        assert entry["input_tokens"] > 0
        assert entry["output_tokens"] > 0
        assert entry["total_tokens"] > 0
        assert entry["cost"] > 0

    @pytest.mark.asyncio
    async def test_history_persists_across_chats(self, mocker):
        """Test that conversation history persists across multiple chats"""
        agent = WYN360Agent(api_key="test_key", use_history=True)

        mock_result = Mock()
        mock_result.data = None  # Set data to None so it falls back to output
        mock_result.output = "Response"
        mocker.patch.object(agent.agent, 'run', return_value=mock_result)

        # First chat
        await agent.chat("First message")
        assert len(agent.conversation_history) == 2  # user + assistant

        # Second chat
        await agent.chat("Second message")
        assert len(agent.conversation_history) == 4  # 2 more messages

        # Check order
        assert agent.conversation_history[0]["content"] == "First message"
        assert agent.conversation_history[1]["content"] == "Response"
        assert agent.conversation_history[2]["content"] == "Second message"
        assert agent.conversation_history[3]["content"] == "Response"


class TestGitTools:
    """Tests for git operation tools"""

    @pytest.mark.asyncio
    async def test_git_status(self):
        """Test git_status tool"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.git_status(None)

        # Should return git status (in a git repo)
        assert "Git Status" in result or "Error" in result

    @pytest.mark.asyncio
    async def test_git_diff_no_changes(self):
        """Test git_diff with no changes"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.git_diff(None)

        # Should return diff or no changes message
        assert "Git Diff" in result or "No changes" in result or "Error" in result

    @pytest.mark.asyncio
    async def test_git_diff_specific_file(self):
        """Test git_diff for specific file"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.git_diff(None, "README.md")

        # Should return diff for specific file
        assert "Git Diff" in result or "No changes" in result or "Error" in result

    @pytest.mark.asyncio
    async def test_git_log(self):
        """Test git_log tool"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.git_log(None, max_count=5)

        # Should return recent commits
        assert "Recent Commits" in result or "Error" in result

    @pytest.mark.asyncio
    async def test_git_branch(self):
        """Test git_branch tool"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.git_branch(None)

        # Should return branch list
        assert "Git Branches" in result or "Error" in result


class TestSearchTool:
    """Tests for search_files tool"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = Path.cwd()
        import os
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up after tests"""
        import os
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    @pytest.mark.asyncio
    async def test_search_files_finds_pattern(self):
        """Test search_files finds matching pattern"""
        # Create test files with content
        (Path(self.test_dir) / "test1.py").write_text("class User:\n    pass")
        (Path(self.test_dir) / "test2.py").write_text("def hello():\n    print('hi')")

        agent = WYN360Agent(api_key="test_key")
        result = await agent.search_files(None, "class User", "*.py")

        assert "test1.py" in result or "Search Results" in result

    @pytest.mark.asyncio
    async def test_search_files_no_matches(self):
        """Test search_files when no matches found"""
        # Create test file without the pattern
        (Path(self.test_dir) / "test.py").write_text("def hello():\n    pass")

        agent = WYN360Agent(api_key="test_key")
        result = await agent.search_files(None, "NonexistentPattern", "*.py")

        assert "No matches found" in result

    @pytest.mark.asyncio
    async def test_search_files_custom_file_pattern(self):
        """Test search_files with custom file pattern"""
        # Create different file types
        (Path(self.test_dir) / "test.txt").write_text("TODO: fix this")
        (Path(self.test_dir) / "test.py").write_text("print('hello')")

        agent = WYN360Agent(api_key="test_key")
        result = await agent.search_files(None, "TODO", "*.txt")

        # Should find TODO in .txt file only
        assert "test.txt" in result or "TODO" in result


class TestFileManagementTools:
    """Tests for file management tools"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = Path.cwd()
        import os
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up after tests"""
        import os
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    @pytest.mark.asyncio
    async def test_delete_file_success(self):
        """Test delete_file successfully deletes a file"""
        # Create test file
        test_file = Path(self.test_dir) / "to_delete.txt"
        test_file.write_text("delete me")

        agent = WYN360Agent(api_key="test_key")
        result = await agent.delete_file(None, str(test_file))

        assert "Successfully deleted" in result
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_file_not_exists(self):
        """Test delete_file when file doesn't exist"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.delete_file(None, "nonexistent.txt")

        assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_move_file_success(self):
        """Test move_file successfully moves a file"""
        # Create source file
        source = Path(self.test_dir) / "source.txt"
        source.write_text("content")

        dest = Path(self.test_dir) / "destination.txt"

        agent = WYN360Agent(api_key="test_key")
        result = await agent.move_file(None, str(source), str(dest))

        assert "Successfully moved" in result
        assert not source.exists()
        assert dest.exists()
        assert dest.read_text() == "content"

    @pytest.mark.asyncio
    async def test_move_file_source_not_exists(self):
        """Test move_file when source doesn't exist"""
        agent = WYN360Agent(api_key="test_key")
        result = await agent.move_file(None, "nonexistent.txt", "dest.txt")

        assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_move_file_dest_exists(self):
        """Test move_file when destination already exists"""
        source = Path(self.test_dir) / "source.txt"
        source.write_text("content")

        dest = Path(self.test_dir) / "dest.txt"
        dest.write_text("existing")

        agent = WYN360Agent(api_key="test_key")
        result = await agent.move_file(None, str(source), str(dest))

        assert "already exists" in result

    @pytest.mark.asyncio
    async def test_move_file_creates_parent_dirs(self):
        """Test move_file creates parent directories"""
        source = Path(self.test_dir) / "source.txt"
        source.write_text("content")

        dest = Path(self.test_dir) / "nested" / "dirs" / "dest.txt"

        agent = WYN360Agent(api_key="test_key")
        result = await agent.move_file(None, str(source), str(dest))

        assert "Successfully moved" in result
        assert dest.exists()

    @pytest.mark.asyncio
    async def test_create_directory_success(self):
        """Test create_directory creates a new directory"""
        new_dir = Path(self.test_dir) / "new_directory"

        agent = WYN360Agent(api_key="test_key")
        result = await agent.create_directory(None, str(new_dir))

        assert "Successfully created" in result
        assert new_dir.exists()
        assert new_dir.is_dir()

    @pytest.mark.asyncio
    async def test_create_directory_nested(self):
        """Test create_directory with nested path"""
        nested_dir = Path(self.test_dir) / "level1" / "level2" / "level3"

        agent = WYN360Agent(api_key="test_key")
        result = await agent.create_directory(None, str(nested_dir))

        assert "Successfully created" in result
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    @pytest.mark.asyncio
    async def test_create_directory_already_exists(self):
        """Test create_directory when directory already exists"""
        existing_dir = Path(self.test_dir) / "existing"
        existing_dir.mkdir()

        agent = WYN360Agent(api_key="test_key")
        result = await agent.create_directory(None, str(existing_dir))

        assert "already exists" in result


class TestModelSwitching:
    """Tests for model switching functionality"""

    def test_get_model_info_default(self):
        """Test get_model_info returns correct info for default model"""
        agent = WYN360Agent(api_key="test_key", model="claude-sonnet-4-20250514")
        info = agent.get_model_info()

        assert info["current_model"] == "claude-sonnet-4-20250514"
        assert info["display_name"] == "Sonnet 4"
        assert info["input_cost_per_million"] == 3.00
        assert info["output_cost_per_million"] == 15.00
        assert "Balanced" in info["description"]

    def test_get_model_info_haiku(self):
        """Test get_model_info for Haiku model"""
        agent = WYN360Agent(api_key="test_key", model="claude-3-5-haiku-20241022")
        info = agent.get_model_info()

        assert info["display_name"] == "Haiku"
        assert info["input_cost_per_million"] == 0.25
        assert info["output_cost_per_million"] == 1.25
        assert "Fast" in info["description"]

    def test_switch_model_short_name(self):
        """Test switching model using short name"""
        agent = WYN360Agent(api_key="test_key", model="claude-sonnet-4-20250514")

        # Switch to haiku using short name
        success = agent.switch_model("haiku")
        assert success is True

        # Verify model changed
        info = agent.get_model_info()
        assert info["display_name"] == "Haiku"
        assert agent.model_name == "claude-3-5-haiku-20241022"

    def test_switch_model_full_name(self):
        """Test switching model using full model ID"""
        agent = WYN360Agent(api_key="test_key", model="claude-sonnet-4-20250514")

        # Switch using full name
        success = agent.switch_model("claude-3-5-haiku-20241022")
        assert success is True

        # Verify model changed
        assert agent.model_name == "claude-3-5-haiku-20241022"

    def test_switch_model_case_insensitive(self):
        """Test model switching is case insensitive"""
        agent = WYN360Agent(api_key="test_key")

        # Try different cases
        success1 = agent.switch_model("HAIKU")
        assert success1 is True

        success2 = agent.switch_model("Sonnet")
        assert success2 is True

        success3 = agent.switch_model("oPuS")
        assert success3 is True

    def test_switch_model_preserves_history(self):
        """Test that switching models preserves conversation history"""
        agent = WYN360Agent(api_key="test_key")

        # Add some history
        agent.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]

        # Switch model
        agent.switch_model("haiku")

        # History should still be there
        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[0]["content"] == "Hello"

    def test_model_description(self):
        """Test _get_model_description method"""
        agent = WYN360Agent(api_key="test_key")

        desc_haiku = agent._get_model_description("claude-3-5-haiku-20241022")
        assert "Fast" in desc_haiku

        desc_sonnet = agent._get_model_description("claude-sonnet-4-20250514")
        assert "Balanced" in desc_sonnet

        desc_opus = agent._get_model_description("claude-opus-4-20250514")
        assert "capable" in desc_opus

        desc_unknown = agent._get_model_description("unknown-model")
        assert "Custom" in desc_unknown


class TestStreaming:
    """Tests for streaming functionality"""

    def test_chat_stream_method_exists(self):
        """Test that chat_stream method exists"""
        agent = WYN360Agent(api_key="test_key")

        assert hasattr(agent, 'chat_stream')
        assert callable(agent.chat_stream)

    @pytest.mark.asyncio
    async def test_chat_stream_returns_complete_response(self):
        """Test that chat_stream returns complete response text"""
        agent = WYN360Agent(api_key="test_key")

        # Mock run() to return a complete response
        class MockResult:
            data = "Hello World"

        async def mock_run(*args, **kwargs):
            return MockResult()

        # Patch the agent's run method
        agent.agent.run = mock_run

        # Test chat_stream
        response = await agent.chat_stream("Test message")

        # Verify we got complete response string
        assert isinstance(response, str)
        assert response == "Hello World"

        # Verify conversation history was updated
        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[0]["role"] == "user"
        assert agent.conversation_history[0]["content"] == "Test message"
        assert agent.conversation_history[1]["role"] == "assistant"
        assert agent.conversation_history[1]["content"] == "Hello World"

    @pytest.mark.asyncio
    async def test_chat_stream_handles_errors(self):
        """Test that chat_stream handles errors gracefully"""
        agent = WYN360Agent(api_key="test_key")

        # Mock run() to raise an error
        async def mock_run_error(*args, **kwargs):
            raise Exception("Test error")

        agent.agent.run = mock_run_error

        # Test that error is returned
        response = await agent.chat_stream("Test message")

        # Should return error message
        assert isinstance(response, str)
        assert "error" in response.lower()
        assert "test error" in response.lower()


class TestHuggingFaceTools:
    """Tests for HuggingFace integration tools"""

    @pytest.mark.asyncio
    async def test_check_hf_authentication_not_authenticated(self, mocker):
        """Test authentication check when not authenticated"""
        agent = WYN360Agent(api_key="test_key")

        # Mock execute_command_safe to simulate not authenticated
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(False, "not logged in", 1)
        )

        result = await agent.check_hf_authentication(None)

        assert "Not authenticated" in result
        assert "https://huggingface.co/settings/tokens" in result

    @pytest.mark.asyncio
    async def test_check_hf_authentication_authenticated(self, mocker):
        """Test authentication check when authenticated"""
        agent = WYN360Agent(api_key="test_key")

        # Mock execute_command_safe to simulate authenticated
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(True, "username: testuser\nemail: test@example.com", 0)
        )

        result = await agent.check_hf_authentication(None)

        assert "Authenticated" in result
        assert "testuser" in result

    @pytest.mark.asyncio
    async def test_check_hf_authentication_auto_auth(self, mocker):
        """Test auto-authentication when HF_TOKEN is in environment"""
        agent = WYN360Agent(api_key="test_key")

        # Set HF_TOKEN in environment
        mocker.patch.dict('os.environ', {'HF_TOKEN': 'hf_test_token_12345'})

        # Mock execute_command_safe to simulate:
        # 1. whoami fails (not authenticated yet)
        # 2. auth login succeeds
        # 3. whoami succeeds after authentication
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (False, "not logged in", 1),  # First whoami fails
            (True, "Token is valid", 0),   # auth login succeeds
            (True, "username: autouser\nemail: auto@example.com", 0)  # Second whoami succeeds
        ]

        result = await agent.check_hf_authentication(None)

        assert "Authenticated" in result
        assert "autouser" in result
        assert "auto-authenticated" in result.lower()

    @pytest.mark.asyncio
    async def test_authenticate_hf_invalid_token(self):
        """Test authentication with invalid token"""
        agent = WYN360Agent(api_key="test_key")

        result = await agent.authenticate_hf(None, "short")

        assert "Invalid token" in result

    @pytest.mark.asyncio
    async def test_authenticate_hf_success(self, mocker):
        """Test successful authentication"""
        agent = WYN360Agent(api_key="test_key")

        # Mock both auth login and whoami commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "token is valid", 0),  # auth login
            (True, "username: testuser", 0)  # whoami
        ]

        result = await agent.authenticate_hf(None, "hf_validtoken1234567890")

        assert "Successfully authenticated" in result
        assert "testuser" in result

    @pytest.mark.asyncio
    async def test_authenticate_hf_failure(self, mocker):
        """Test failed authentication"""
        agent = WYN360Agent(api_key="test_key")

        # Mock auth login failure
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(False, "invalid token", 1)
        )

        result = await agent.authenticate_hf(None, "hf_invalidtoken")

        assert "Authentication failed" in result

    @pytest.mark.asyncio
    async def test_create_hf_readme_streamlit(self, mocker, tmp_path):
        """Test README creation for Streamlit app"""
        agent = WYN360Agent(api_key="test_key")

        # Change to temp directory
        import os
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = await agent.create_hf_readme(
                None,
                title="Test Echo Bot",
                sdk="streamlit",
                sdk_version="1.34.0",
                app_file="app.py"
            )

            assert "Created README.md" in result
            assert "streamlit" in result.lower()

            # Verify README.md was created
            readme_path = tmp_path / "README.md"
            assert readme_path.exists()

            # Verify frontmatter content
            content = readme_path.read_text()
            assert "title: Test Echo Bot" in content
            assert "sdk: streamlit" in content
            assert "sdk_version: 1.34.0" in content
            assert "app_file: app.py" in content
            assert "---" in content  # YAML frontmatter markers
        finally:
            os.chdir(original_dir)

    @pytest.mark.asyncio
    async def test_create_hf_readme_gradio(self, mocker, tmp_path):
        """Test README creation for Gradio app"""
        agent = WYN360Agent(api_key="test_key")

        import os
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = await agent.create_hf_readme(
                None,
                title="Gradio Demo",
                sdk="gradio",
                emoji="🎨",
                color_from="blue",
                color_to="purple"
            )

            assert "Created README.md" in result
            assert "gradio" in result.lower()

            # Verify content
            readme_path = tmp_path / "README.md"
            content = readme_path.read_text()
            assert "sdk: gradio" in content
            assert "emoji: 🎨" in content
            assert "colorFrom: blue" in content
            assert "colorTo: purple" in content
        finally:
            os.chdir(original_dir)

    @pytest.mark.asyncio
    async def test_create_hf_space_success(self, mocker):
        """Test successful Space creation"""
        agent = WYN360Agent(api_key="test_key")

        # Mock execute_command_safe to simulate successful space creation
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(True, "Repository created successfully", 0)
        )

        result = await agent.create_hf_space(None, "eagle0504/test-app", sdk="streamlit")

        assert "Successfully created" in result
        assert "eagle0504/test-app" in result
        assert "https://huggingface.co/spaces/eagle0504/test-app" in result

    @pytest.mark.asyncio
    async def test_create_hf_space_already_exists(self, mocker):
        """Test Space creation when space already exists"""
        agent = WYN360Agent(api_key="test_key")

        # Mock execute_command_safe to simulate space already exists
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(False, "Repository already exists", 1)
        )

        result = await agent.create_hf_space(None, "eagle0504/existing-app")

        assert "already exists" in result
        assert "eagle0504/existing-app" in result

    @pytest.mark.asyncio
    async def test_create_hf_space_invalid_name(self):
        """Test Space creation with invalid name format"""
        agent = WYN360Agent(api_key="test_key")

        result = await agent.create_hf_space(None, "invalidname")

        assert "Invalid space name format" in result
        assert "username/repo-name" in result

    @pytest.mark.asyncio
    async def test_push_to_hf_space_success(self, mocker, tmp_path):
        """Test successful file upload to Space"""
        agent = WYN360Agent(api_key="test_key")

        # Create test directory with app.py
        test_dir = tmp_path / "test_app"
        test_dir.mkdir()
        (test_dir / "app.py").write_text("import streamlit as st")
        (test_dir / "requirements.txt").write_text("streamlit")

        # Mock execute_command_safe to simulate successful upload
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(True, "Files uploaded successfully", 0)
        )

        result = await agent.push_to_hf_space(None, "eagle0504/test-app", str(test_dir))

        assert "Successfully uploaded" in result
        assert "🎉" in result
        assert "https://huggingface.co/spaces/eagle0504/test-app" in result

    @pytest.mark.asyncio
    async def test_push_to_hf_space_directory_not_found(self):
        """Test upload with non-existent directory"""
        agent = WYN360Agent(api_key="test_key")

        result = await agent.push_to_hf_space(None, "eagle0504/test-app", "/nonexistent/path")

        assert "Directory not found" in result

    @pytest.mark.asyncio
    async def test_push_to_hf_space_invalid_name(self):
        """Test upload with invalid space name"""
        agent = WYN360Agent(api_key="test_key")

        result = await agent.push_to_hf_space(None, "invalidname", ".")

        assert "Invalid space name format" in result


class TestGenerateTests:
    """Tests for test generation tool"""

    @pytest.mark.asyncio
    async def test_generate_tests_simple_function(self, tmp_path):
        """Test generating tests for simple functions"""
        agent = WYN360Agent(api_key="test_key")

        # Create a simple Python file
        test_file = tmp_path / "calculator.py"
        test_file.write_text("""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")

        result = await agent.generate_tests(None, str(test_file))

        assert "✓ Generated test file" in result
        assert "test_calculator.py" in result
        assert "2 function(s)" in result
        assert "add, subtract" in result

        # Verify test file was created
        test_output = tmp_path / "test_calculator.py"
        assert test_output.exists()
        content = test_output.read_text()
        assert "def test_add_basic():" in content
        assert "def test_subtract_basic():" in content
        assert "import pytest" in content

    @pytest.mark.asyncio
    async def test_generate_tests_class(self, tmp_path):
        """Test generating tests for classes"""
        agent = WYN360Agent(api_key="test_key")

        # Create a class-based Python file
        test_file = tmp_path / "user.py"
        test_file.write_text("""class User:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}"

    def update_name(self, new_name):
        self.name = new_name
""")

        result = await agent.generate_tests(None, str(test_file))

        assert "✓ Generated test file" in result
        assert "1 class(es): User" in result

        # Verify test file content
        test_output = tmp_path / "test_user.py"
        assert test_output.exists()
        content = test_output.read_text()
        assert "class TestUser:" in content
        assert "def test_initialization(self):" in content
        assert "def test_greet(self):" in content

    @pytest.mark.asyncio
    async def test_generate_tests_file_not_found(self):
        """Test error handling when file doesn't exist"""
        agent = WYN360Agent(api_key="test_key")

        result = await agent.generate_tests(None, "/nonexistent/file.py")

        assert "File not found" in result

    @pytest.mark.asyncio
    async def test_generate_tests_not_python_file(self, tmp_path):
        """Test error handling for non-Python files"""
        agent = WYN360Agent(api_key="test_key")

        # Create a text file
        test_file = tmp_path / "readme.txt"
        test_file.write_text("This is not Python code")

        result = await agent.generate_tests(None, str(test_file))

        assert "must be a Python file" in result

    @pytest.mark.asyncio
    async def test_generate_tests_syntax_error(self, tmp_path):
        """Test error handling for Python files with syntax errors"""
        agent = WYN360Agent(api_key="test_key")

        # Create a Python file with syntax error
        test_file = tmp_path / "broken.py"
        test_file.write_text("""def broken_function(
    # Missing closing parenthesis
    return "broken"
""")

        result = await agent.generate_tests(None, str(test_file))

        assert "Syntax error" in result

    @pytest.mark.asyncio
    async def test_generate_tests_custom_output_path(self, tmp_path):
        """Test generating tests with custom output path"""
        agent = WYN360Agent(api_key="test_key")

        # Create a simple Python file
        test_file = tmp_path / "math_utils.py"
        test_file.write_text("""def multiply(a, b):
    return a * b
""")

        custom_output = tmp_path / "tests" / "test_math.py"
        custom_output.parent.mkdir(exist_ok=True)

        result = await agent.generate_tests(None, str(test_file), str(custom_output))

        assert "✓ Generated test file" in result
        assert str(custom_output) in result
        assert custom_output.exists()


class TestGitHubTools:
    """Tests for GitHub integration tools (Phase 8.1)"""

    @pytest.mark.asyncio
    async def test_check_gh_authentication_not_authenticated(self, mocker):
        """Test GitHub authentication check when not authenticated"""
        agent = WYN360Agent(api_key="test_key")

        # Mock execute_command_safe to simulate not authenticated
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (False, "not logged in", 1),  # gh auth status fails
        ]

        # No GH_TOKEN in environment
        mocker.patch.dict('os.environ', {}, clear=True)

        result = await agent.check_gh_authentication(None)

        assert "Not authenticated" in result
        assert "https://github.com/settings/tokens" in result

    @pytest.mark.asyncio
    async def test_check_gh_authentication_authenticated(self, mocker):
        """Test GitHub authentication check when authenticated"""
        agent = WYN360Agent(api_key="test_key")

        # Mock execute_command_safe to simulate authenticated
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(True, "✓ Logged in to github.com as testuser", 0)
        )

        result = await agent.check_gh_authentication(None)

        assert "Authenticated" in result
        assert "testuser" in result

    @pytest.mark.asyncio
    async def test_check_gh_authentication_auto_auth(self, mocker):
        """Test auto-authentication when GH_TOKEN is in environment"""
        agent = WYN360Agent(api_key="test_key")

        # Set GH_TOKEN in environment
        mocker.patch.dict('os.environ', {'GH_TOKEN': 'ghp_test_token_12345'})

        # Mock execute_command_safe to simulate:
        # 1. gh auth status fails (not authenticated yet)
        # 2. auth login succeeds
        # 3. gh auth status succeeds (verification)
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (False, "not logged in", 1),  # First status check fails
            (True, "Authentication complete", 0),   # auth login succeeds
            (True, "✓ Logged in to github.com", 0),  # Second status check succeeds
        ]

        result = await agent.check_gh_authentication(None)

        assert "Authenticated" in result
        assert "auto-authenticated" in result.lower()

    @pytest.mark.asyncio
    async def test_authenticate_gh_invalid_token(self):
        """Test GitHub authentication with invalid token"""
        agent = WYN360Agent(api_key="test_key")

        result = await agent.authenticate_gh(None, "short")

        assert "Invalid token" in result

    @pytest.mark.asyncio
    async def test_authenticate_gh_success(self, mocker):
        """Test successful GitHub authentication"""
        agent = WYN360Agent(api_key="test_key")

        # Mock auth login success
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(True, "Authentication complete", 0)
        )

        result = await agent.authenticate_gh(None, "ghp_validtoken1234567890")

        assert "Successfully authenticated" in result
        assert "GitHub features" in result

    @pytest.mark.asyncio
    async def test_authenticate_gh_failure(self, mocker):
        """Test failed GitHub authentication"""
        agent = WYN360Agent(api_key="test_key")

        # Mock auth login failure
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(False, "invalid token", 1)
        )

        result = await agent.authenticate_gh(None, "ghp_invalidtoken")

        assert "Authentication failed" in result

    @pytest.mark.asyncio
    async def test_gh_commit_changes_success(self, mocker):
        """Test successful commit and push"""
        agent = WYN360Agent(api_key="test_key")

        # Mock git commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "", 0),  # git rev-parse --git-dir
            (True, "M file.py\nA new_file.py", 0),  # git status --porcelain (has changes)
            (True, "", 0),  # git add -A
            (True, "[main abc123] Test commit", 0),  # git commit
            (True, "origin\tgit@github.com:user/repo.git (fetch)", 0),  # git remote -v
            (True, "main", 0),  # git branch --show-current
            (True, "To github.com:user/repo.git", 0),  # git push
        ]

        result = await agent.gh_commit_changes(None, "Test commit", push=True)

        assert "Successfully committed" in result
        assert "pushed" in result.lower()

    @pytest.mark.asyncio
    async def test_gh_commit_changes_not_a_repo(self, mocker):
        """Test commit when not in a git repository"""
        agent = WYN360Agent(api_key="test_key")

        # Mock git rev-parse failure
        mocker.patch(
            'wyn360_cli.utils.execute_command_safe',
            return_value=(False, "not a git repository", 128)
        )

        result = await agent.gh_commit_changes(None, "Test commit")

        assert "Not a git repository" in result

    @pytest.mark.asyncio
    async def test_gh_create_pr_success(self, mocker):
        """Test successful PR creation"""
        agent = WYN360Agent(api_key="test_key")

        # Mock commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "✓ Logged in", 0),  # gh auth status
            (True, "feature/test", 0),  # git branch --show-current
            (True, "https://github.com/user/repo/pull/42", 0),  # gh pr create
        ]

        result = await agent.gh_create_pr(None, "Test PR", "Description", "main")

        assert "Successfully created pull request" in result
        assert "https://github.com/user/repo/pull/42" in result

    @pytest.mark.asyncio
    async def test_gh_create_pr_on_main_branch(self, mocker):
        """Test PR creation fails when on main branch"""
        agent = WYN360Agent(api_key="test_key")

        # Mock commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "✓ Logged in", 0),  # gh auth status
            (True, "main", 0),  # git branch --show-current
        ]

        result = await agent.gh_create_pr(None, "Test PR", "Description", "main")

        assert "Cannot create PR" in result
        assert "from 'main' to itself" in result

    @pytest.mark.asyncio
    async def test_gh_create_branch_success(self, mocker):
        """Test successful branch creation"""
        agent = WYN360Agent(api_key="test_key")

        # Mock git commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "", 0),  # git rev-parse --git-dir
            (False, "fatal: Needed a single revision", 128),  # git rev-parse --verify (branch doesn't exist)
            (True, "Switched to a new branch 'feature/test'", 0),  # git checkout -b
        ]

        result = await agent.gh_create_branch(None, "feature/test", checkout=True)

        assert "Created" in result
        assert "switched" in result
        assert "feature/test" in result

    @pytest.mark.asyncio
    async def test_gh_create_branch_no_checkout(self, mocker):
        """Test branch creation without checkout"""
        agent = WYN360Agent(api_key="test_key")

        # Mock git commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "", 0),  # git rev-parse --git-dir
            (False, "fatal: Needed a single revision", 128),  # git rev-parse --verify (branch doesn't exist)
            (True, "", 0),  # git branch
        ]

        result = await agent.gh_create_branch(None, "feature/test", checkout=False)

        assert "Created new branch" in result
        assert "feature/test" in result

    @pytest.mark.asyncio
    async def test_gh_checkout_branch_success(self, mocker):
        """Test successful branch checkout"""
        agent = WYN360Agent(api_key="test_key")

        # Mock git commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "", 0),  # git rev-parse --git-dir
            (True, "main", 0),  # git branch --show-current
            (True, "", 0),  # git status --porcelain (no uncommitted changes)
            (True, "Switched to branch 'feature/test'", 0),  # git checkout
        ]

        result = await agent.gh_checkout_branch(None, "feature/test")

        assert "Switched to branch" in result
        assert "feature/test" in result

    @pytest.mark.asyncio
    async def test_gh_checkout_branch_not_exists(self, mocker):
        """Test checkout when branch doesn't exist"""
        agent = WYN360Agent(api_key="test_key")

        # Mock git commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "", 0),  # git rev-parse --git-dir
            (True, "main", 0),  # git branch --show-current
            (True, "", 0),  # git status --porcelain (no uncommitted changes)
            (False, "error: pathspec 'nonexistent' did not match any file(s) known to git", 1),  # git checkout fails
        ]

        result = await agent.gh_checkout_branch(None, "nonexistent")

        assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_gh_merge_branch_success(self, mocker):
        """Test successful branch merge"""
        agent = WYN360Agent(api_key="test_key")

        # Mock git commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "", 0),  # git rev-parse --git-dir
            (True, "main", 0),  # git branch --show-current
            (True, "", 0),  # git status --porcelain (clean, no uncommitted changes)
            (True, "Updating abc123..def456\nFast-forward", 0),  # git merge
        ]

        result = await agent.gh_merge_branch(None, "feature/test", "main")

        assert "Successfully merged" in result
        assert "feature/test" in result
        assert "main" in result

    @pytest.mark.asyncio
    async def test_gh_merge_branch_wrong_branch(self, mocker):
        """Test merge fails when on wrong branch"""
        agent = WYN360Agent(api_key="test_key")

        # Mock: currently on feature branch, trying to merge main into develop, but checkout fails
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "", 0),  # git rev-parse --git-dir
            (True, "feature/test", 0),  # git branch --show-current (on wrong branch)
            (False, "error: pathspec 'develop' did not match any file(s) known to git", 1),  # git checkout develop fails
        ]

        result = await agent.gh_merge_branch(None, "main", "develop")

        assert "Failed to switch to target branch" in result

    @pytest.mark.asyncio
    async def test_gh_merge_branch_conflict(self, mocker):
        """Test merge with conflicts"""
        agent = WYN360Agent(api_key="test_key")

        # Mock git commands
        mock_execute = mocker.patch('wyn360_cli.utils.execute_command_safe')
        mock_execute.side_effect = [
            (True, "", 0),  # git rev-parse --git-dir
            (True, "main", 0),  # git branch --show-current
            (True, "", 0),  # git status --porcelain (clean, no uncommitted changes)
            (False, "CONFLICT (content): Merge conflict in file.py", 1),  # git merge fails
        ]

        result = await agent.gh_merge_branch(None, "feature/test", "main")

        assert "conflict" in result.lower() or "failed" in result.lower()
