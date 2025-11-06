"""Unit tests for utils.py"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from wyn360_cli.utils import (
    extract_code_blocks,
    scan_directory,
    read_file_safe,
    write_file_safe,
    get_project_summary,
    is_blank_project,
    execute_command_safe
)


class TestExtractCodeBlocks:
    """Tests for extract_code_blocks function"""

    def test_extract_single_python_block(self):
        text = """
Here is some Python code:
```python
def hello():
    print("Hello, World!")
```
        """
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]['language'] == 'python'
        assert 'def hello():' in blocks[0]['code']

    def test_extract_multiple_blocks(self):
        text = """
```python
print("First")
```

Some text in between.

```javascript
console.log("Second");
```
        """
        blocks = extract_code_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]['language'] == 'python'
        assert blocks[1]['language'] == 'javascript'

    def test_extract_no_blocks(self):
        text = "Just some regular text without code blocks."
        blocks = extract_code_blocks(text)
        assert len(blocks) == 0

    def test_extract_block_without_language(self):
        text = """
```
some code without language specified
```
        """
        blocks = extract_code_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]['language'] == 'python'  # Default


class TestScanDirectory:
    """Tests for scan_directory function"""

    def setup_method(self):
        """Create a temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_scan_empty_directory(self):
        files = scan_directory(self.test_dir)
        assert files['python'] == []
        assert files['text'] == []
        assert files['config'] == []
        assert files['other'] == []

    def test_scan_directory_with_python_files(self):
        # Create test files
        py_file = Path(self.test_dir) / "test.py"
        py_file.write_text("print('hello')")

        files = scan_directory(self.test_dir)
        assert len(files['python']) == 1
        assert 'test.py' in files['python'][0]

    def test_scan_directory_with_multiple_types(self):
        # Create various file types
        (Path(self.test_dir) / "script.py").write_text("code")
        (Path(self.test_dir) / "readme.md").write_text("docs")
        (Path(self.test_dir) / "config.json").write_text("{}")
        (Path(self.test_dir) / "data.csv").write_text("csv")

        files = scan_directory(self.test_dir)
        assert len(files['python']) == 1
        assert len(files['text']) == 1
        assert len(files['config']) == 1
        assert len(files['other']) == 1

    def test_scan_directory_ignores_patterns(self):
        # Create files that should be ignored
        pycache = Path(self.test_dir) / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("bytecode")

        files = scan_directory(self.test_dir)
        # Should not include __pycache__ files
        assert not any('__pycache__' in str(f) for f in files['python'])


class TestReadFileSafe:
    """Tests for read_file_safe function"""

    def setup_method(self):
        """Create a temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_read_existing_file(self):
        file_path = Path(self.test_dir) / "test.txt"
        content = "Hello, World!"
        file_path.write_text(content)

        success, result = read_file_safe(str(file_path))
        assert success is True
        assert result == content

    def test_read_nonexistent_file(self):
        file_path = Path(self.test_dir) / "nonexistent.txt"
        success, result = read_file_safe(str(file_path))
        assert success is False
        assert "not found" in result.lower()

    def test_read_file_size_limit(self):
        file_path = Path(self.test_dir) / "large.txt"
        # Create a file larger than limit
        content = "x" * 2000  # 2KB
        file_path.write_text(content)

        # Try to read with small limit
        success, result = read_file_safe(str(file_path), max_size=1000)
        assert success is False
        assert "too large" in result.lower()


class TestWriteFileSafe:
    """Tests for write_file_safe function"""

    def setup_method(self):
        """Create a temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_write_new_file(self):
        file_path = Path(self.test_dir) / "new.txt"
        content = "Test content"

        success, message = write_file_safe(str(file_path), content)
        assert success is True
        assert "Successfully wrote" in message
        assert file_path.read_text() == content

    def test_write_existing_file_no_overwrite(self):
        file_path = Path(self.test_dir) / "existing.txt"
        file_path.write_text("Original")

        success, message = write_file_safe(str(file_path), "New", overwrite=False)
        assert success is False
        assert "already exists" in message
        assert file_path.read_text() == "Original"

    def test_write_existing_file_with_overwrite(self):
        file_path = Path(self.test_dir) / "existing.txt"
        file_path.write_text("Original")

        success, message = write_file_safe(str(file_path), "New", overwrite=True)
        assert success is True
        assert file_path.read_text() == "New"

    def test_write_creates_parent_directories(self):
        file_path = Path(self.test_dir) / "subdir" / "nested" / "file.txt"
        content = "Nested content"

        success, message = write_file_safe(str(file_path), content)
        assert success is True
        assert file_path.exists()
        assert file_path.read_text() == content


class TestGetProjectSummary:
    """Tests for get_project_summary function"""

    def setup_method(self):
        """Create a temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_summary_of_empty_project(self):
        summary = get_project_summary(self.test_dir)
        assert "Total files: 0" in summary
        assert "Project Summary" in summary

    def test_summary_with_files(self):
        # Create some test files
        (Path(self.test_dir) / "main.py").write_text("code")
        (Path(self.test_dir) / "readme.md").write_text("docs")

        summary = get_project_summary(self.test_dir)
        assert "Total files: 2" in summary
        assert "PYTHON" in summary or "python" in summary


class TestIsBlankProject:
    """Tests for is_blank_project function"""

    def setup_method(self):
        """Create a temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_blank_project_empty_directory(self):
        assert is_blank_project(self.test_dir) is True

    def test_blank_project_only_config(self):
        (Path(self.test_dir) / "config.json").write_text("{}")
        assert is_blank_project(self.test_dir) is True

    def test_not_blank_with_python_files(self):
        (Path(self.test_dir) / "main.py").write_text("code")
        assert is_blank_project(self.test_dir) is False

    def test_not_blank_with_text_files(self):
        (Path(self.test_dir) / "readme.md").write_text("docs")
        assert is_blank_project(self.test_dir) is False


class TestExecuteCommandSafe:
    """Tests for execute_command_safe function"""

    def setup_method(self):
        """Create a temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_execute_successful_command(self):
        """Test executing a successful command"""
        success, output, return_code = execute_command_safe("echo 'Hello World'")
        assert success is True
        assert "Hello World" in output
        assert return_code == 0

    def test_execute_failed_command(self):
        """Test executing a command that fails"""
        success, output, return_code = execute_command_safe("exit 1")
        assert success is False
        assert return_code == 1

    def test_execute_nonexistent_command(self):
        """Test executing a command that doesn't exist"""
        success, output, return_code = execute_command_safe("nonexistent_command_xyz")
        assert success is False
        assert return_code != 0

    def test_execute_with_working_directory(self):
        """Test executing command in specific working directory"""
        # Create a test file in the temp directory
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("content")

        # List files in that directory
        success, output, return_code = execute_command_safe(
            "ls test.txt",
            working_dir=self.test_dir
        )
        assert success is True
        assert "test.txt" in output

    def test_execute_invalid_working_directory(self):
        """Test executing with non-existent working directory"""
        success, output, return_code = execute_command_safe(
            "echo test",
            working_dir="/nonexistent/directory/xyz"
        )
        assert success is False
        assert "not found" in output.lower()
        assert return_code == 1

    def test_execute_timeout(self):
        """Test command timeout"""
        # Command that sleeps for 10 seconds with 1 second timeout
        success, output, return_code = execute_command_safe(
            "sleep 10",
            timeout=1
        )
        assert success is False
        assert "timed out" in output.lower()
        assert return_code == -1

    def test_execute_captures_stderr(self):
        """Test that stderr is captured"""
        # Command that writes to stderr
        success, output, return_code = execute_command_safe(
            "python -c \"import sys; sys.stderr.write('error message')\"",
            working_dir=self.test_dir
        )
        # Python exits with 0 even when writing to stderr
        assert "error message" in output

    def test_execute_python_script(self):
        """Test executing a Python script"""
        # Create a simple Python script
        script_path = Path(self.test_dir) / "test_script.py"
        script_path.write_text("print('Script executed')")

        success, output, return_code = execute_command_safe(
            "python test_script.py",
            working_dir=self.test_dir
        )
        assert success is True
        assert "Script executed" in output
        assert return_code == 0


class TestExtractUsernameFromHFWhoami:
    """Tests for extract_username_from_hf_whoami utility function"""

    def test_extract_username_with_colon(self):
        """Test extracting username from output with colon format"""
        from wyn360_cli.utils import extract_username_from_hf_whoami

        output = "username: testuser\nemail: test@example.com"
        username = extract_username_from_hf_whoami(output)

        assert username == "testuser"

    def test_extract_username_without_colon(self):
        """Test extracting username from output without colon"""
        from wyn360_cli.utils import extract_username_from_hf_whoami

        output = "username testuser\nemail test@example.com"
        username = extract_username_from_hf_whoami(output)

        assert username == "testuser"

    def test_extract_username_with_extra_spaces(self):
        """Test extracting username with extra whitespace"""
        from wyn360_cli.utils import extract_username_from_hf_whoami

        output = "  username:   testuser  \nemail: test@example.com"
        username = extract_username_from_hf_whoami(output)

        assert username == "testuser"

    def test_extract_username_not_found(self):
        """Test when username is not in output"""
        from wyn360_cli.utils import extract_username_from_hf_whoami

        output = "some other output\nwithout username"
        username = extract_username_from_hf_whoami(output)

        assert username == "user"  # Default fallback

    def test_extract_username_case_insensitive(self):
        """Test username extraction is case insensitive"""
        from wyn360_cli.utils import extract_username_from_hf_whoami

        output = "USERNAME: TESTUSER\nEMAIL: TEST@EXAMPLE.COM"
        username = extract_username_from_hf_whoami(output)

        assert username == "TESTUSER"
