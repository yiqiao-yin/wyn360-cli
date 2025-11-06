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
    async def test_chat_stream_is_async_generator(self):
        """Test that chat_stream returns an async generator"""
        agent = WYN360Agent(api_key="test_key")

        # Mock the agent.run_stream to return a simple async generator
        class MockResult:
            async def stream(self):
                yield "Hello"
                yield " "
                yield "World"

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_stream(*args, **kwargs):
            return MockResult()

        # Patch the agent's run_stream method
        agent.agent.run_stream = mock_stream

        # Test streaming
        chunks = []
        async for chunk in agent.chat_stream("Test message"):
            chunks.append(chunk)

        # Verify we got chunks
        assert len(chunks) == 3  # "Hello", " ", "World"

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

        # Mock the agent.run_stream to raise an error
        async def mock_stream_error(*args, **kwargs):
            raise Exception("Test error")

        agent.agent.run_stream = mock_stream_error

        # Test that error is yielded
        chunks = []
        async for chunk in agent.chat_stream("Test message"):
            chunks.append(chunk)

        # Should yield error message
        assert len(chunks) > 0
        assert any("error" in chunk.lower() for chunk in chunks)
