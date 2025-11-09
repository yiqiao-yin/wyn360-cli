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
    execute_command_safe,
    PerformanceMetrics
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


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics class (Phase 10.2)"""

    def test_initialization(self):
        """Test PerformanceMetrics initialization"""
        metrics = PerformanceMetrics()

        assert metrics.request_times == []
        assert metrics.tool_calls == {}
        assert metrics.errors == []
        assert metrics.start_time > 0

    def test_track_request_time(self):
        """Test tracking request times"""
        metrics = PerformanceMetrics()

        metrics.track_request_time(1.5)
        metrics.track_request_time(2.3)
        metrics.track_request_time(0.8)

        assert len(metrics.request_times) == 3
        assert metrics.request_times[0][1] == 1.5
        assert metrics.request_times[1][1] == 2.3
        assert metrics.request_times[2][1] == 0.8

    def test_track_tool_call_success(self):
        """Test tracking successful tool calls"""
        metrics = PerformanceMetrics()

        metrics.track_tool_call("read_file", True)
        metrics.track_tool_call("read_file", True)
        metrics.track_tool_call("write_file", True)

        assert "read_file" in metrics.tool_calls
        assert metrics.tool_calls["read_file"]["success"] == 2
        assert metrics.tool_calls["read_file"]["failed"] == 0
        assert metrics.tool_calls["write_file"]["success"] == 1

    def test_track_tool_call_failure(self):
        """Test tracking failed tool calls"""
        metrics = PerformanceMetrics()

        metrics.track_tool_call("read_file", False)
        metrics.track_tool_call("read_file", True)
        metrics.track_tool_call("read_file", False)

        assert metrics.tool_calls["read_file"]["success"] == 1
        assert metrics.tool_calls["read_file"]["failed"] == 2

    def test_track_error(self):
        """Test tracking errors"""
        metrics = PerformanceMetrics()

        metrics.track_error("ValueError", "Invalid input")
        metrics.track_error("FileNotFoundError", "File missing")

        assert len(metrics.errors) == 2
        assert metrics.errors[0]["error_type"] == "ValueError"
        assert metrics.errors[0]["message"] == "Invalid input"
        assert metrics.errors[1]["error_type"] == "FileNotFoundError"

    def test_get_statistics_empty(self):
        """Test getting statistics when no data"""
        metrics = PerformanceMetrics()
        stats = metrics.get_statistics()

        assert stats["total_requests"] == 0
        assert stats["avg_response_time"] == 0.0
        assert stats["total_tool_calls"] == 0
        assert stats["tool_success_rate"] == 0.0
        assert stats["error_count"] == 0

    def test_get_statistics_with_data(self):
        """Test getting statistics with data"""
        import time

        metrics = PerformanceMetrics()

        # Track some request times
        metrics.track_request_time(1.0)
        metrics.track_request_time(2.0)
        metrics.track_request_time(3.0)

        # Track some tool calls
        metrics.track_tool_call("read_file", True)
        metrics.track_tool_call("read_file", True)
        metrics.track_tool_call("write_file", False)
        metrics.track_tool_call("execute_command", True)

        # Track some errors
        metrics.track_error("ValueError", "Test error 1")
        metrics.track_error("ValueError", "Test error 2")
        metrics.track_error("IOError", "Test error 3")

        stats = metrics.get_statistics()

        # Check request statistics
        assert stats["total_requests"] == 3
        assert stats["avg_response_time"] == 2.0
        assert stats["min_response_time"] == 1.0
        assert stats["max_response_time"] == 3.0

        # Check tool statistics
        assert stats["total_tool_calls"] == 4
        assert stats["successful_tool_calls"] == 3
        assert stats["failed_tool_calls"] == 1
        assert stats["tool_success_rate"] == 75.0

        # Check error statistics
        assert stats["error_count"] == 3
        assert stats["error_types"]["ValueError"] == 2
        assert stats["error_types"]["IOError"] == 1

        # Check most used tools
        assert len(stats["most_used_tools"]) == 3
        # read_file should be most used (2 calls)
        assert stats["most_used_tools"][0][0] == "read_file"

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization"""
        metrics = PerformanceMetrics()

        # Add some data
        metrics.track_request_time(1.5)
        metrics.track_tool_call("read_file", True)
        metrics.track_error("ValueError", "Test error")

        # Convert to dict
        data = metrics.to_dict()

        # Create new instance and load from dict
        new_metrics = PerformanceMetrics()
        new_metrics.from_dict(data)

        # Verify data was loaded correctly
        assert len(new_metrics.request_times) == 1
        assert "read_file" in new_metrics.tool_calls
        assert len(new_metrics.errors) == 1

    def test_session_duration(self):
        """Test session duration calculation"""
        import time

        metrics = PerformanceMetrics()

        # Wait a short time
        time.sleep(0.1)

        stats = metrics.get_statistics()

        # Session duration should be > 0
        assert stats["session_duration_seconds"] > 0
        assert stats["session_duration_seconds"] >= 0.1

    def test_most_used_tools_ordering(self):
        """Test that most used tools are ordered correctly"""
        metrics = PerformanceMetrics()

        # Tool A: 5 calls
        for _ in range(5):
            metrics.track_tool_call("tool_a", True)

        # Tool B: 3 calls
        for _ in range(3):
            metrics.track_tool_call("tool_b", True)

        # Tool C: 7 calls
        for _ in range(7):
            metrics.track_tool_call("tool_c", True)

        stats = metrics.get_statistics()

        # Should be ordered by total calls: tool_c (7), tool_a (5), tool_b (3)
        assert stats["most_used_tools"][0][0] == "tool_c"
        assert stats["most_used_tools"][1][0] == "tool_a"
        assert stats["most_used_tools"][2][0] == "tool_b"

    def test_tool_success_rate_calculation(self):
        """Test tool success rate calculation"""
        metrics = PerformanceMetrics()

        # 8 successes, 2 failures = 80% success rate
        for _ in range(8):
            metrics.track_tool_call("test_tool", True)
        for _ in range(2):
            metrics.track_tool_call("test_tool", False)

        stats = metrics.get_statistics()

        assert stats["tool_success_rate"] == 80.0
