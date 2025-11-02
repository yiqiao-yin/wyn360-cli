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
        mock_result.data = "Test response"
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
