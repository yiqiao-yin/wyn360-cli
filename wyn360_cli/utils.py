"""Utility functions for WYN360 CLI"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown text.

    Args:
        text: Text containing markdown code blocks

    Returns:
        List of dictionaries with 'language' and 'code' keys
    """
    # Pattern to match ```language\ncode\n```
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            'language': language or 'python',
            'code': code.strip()
        })

    return code_blocks


def scan_directory(path: str = ".", ignore_patterns: List[str] = None) -> Dict[str, List[str]]:
    """
    Scan directory and categorize files.

    Args:
        path: Directory path to scan (default: current directory)
        ignore_patterns: List of patterns to ignore (e.g., '__pycache__', '.git')

    Returns:
        Dictionary with file categories and their paths
    """
    if ignore_patterns is None:
        ignore_patterns = ['__pycache__', '.git', '.pyc', 'node_modules', '.venv', 'venv']

    directory = Path(path)
    files = {
        'python': [],
        'text': [],
        'config': [],
        'other': []
    }

    for item in directory.rglob('*'):
        if item.is_file():
            # Check if should ignore
            if any(pattern in str(item) for pattern in ignore_patterns):
                continue

            # Categorize by extension
            suffix = item.suffix.lower()
            if suffix == '.py':
                files['python'].append(str(item))
            elif suffix in ['.txt', '.md', '.rst']:
                files['text'].append(str(item))
            elif suffix in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
                files['config'].append(str(item))
            else:
                files['other'].append(str(item))

    return files


def read_file_safe(file_path: str, max_size: int = 1024 * 1024) -> Tuple[bool, str]:
    """
    Safely read a file with size limit.

    Args:
        file_path: Path to file
        max_size: Maximum file size in bytes (default: 1MB)

    Returns:
        Tuple of (success: bool, content or error message: str)
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return False, f"File not found: {file_path}"

        if path.stat().st_size > max_size:
            return False, f"File too large: {file_path} (max {max_size} bytes)"

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        return True, content
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def write_file_safe(file_path: str, content: str, overwrite: bool = False) -> Tuple[bool, str]:
    """
    Safely write content to a file.

    Args:
        file_path: Path to file
        content: Content to write
        overwrite: Whether to overwrite existing files

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        path = Path(file_path)

        # Check if file exists and overwrite is False
        if path.exists() and not overwrite:
            return False, f"File already exists: {file_path}. To update it, call write_file again with overwrite=True"

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True, f"Successfully wrote to: {file_path}"
    except Exception as e:
        return False, f"Error writing file: {str(e)}"


def get_project_summary(path: str = ".") -> str:
    """
    Get a summary of the project structure.

    Args:
        path: Project directory path

    Returns:
        String summary of project
    """
    files = scan_directory(path)

    summary = f"Project Summary for: {os.path.abspath(path)}\n"
    summary += "=" * 60 + "\n\n"

    total_files = sum(len(file_list) for file_list in files.values())
    summary += f"Total files: {total_files}\n\n"

    for category, file_list in files.items():
        if file_list:
            summary += f"{category.upper()} files ({len(file_list)}):\n"
            for file_path in file_list[:10]:  # Show first 10
                summary += f"  - {file_path}\n"
            if len(file_list) > 10:
                summary += f"  ... and {len(file_list) - 10} more\n"
            summary += "\n"

    return summary


def is_blank_project(path: str = ".") -> bool:
    """
    Check if the current directory is a blank project.

    Args:
        path: Directory path to check

    Returns:
        True if directory is empty or only has config files
    """
    files = scan_directory(path)

    # Consider it blank if no Python or text files
    return len(files['python']) == 0 and len(files['text']) == 0


def execute_command_safe(
    command: str,
    timeout: int = 300,
    working_dir: str = "."
) -> Tuple[bool, str, int]:
    """
    Safely execute a shell command with timeout.

    This function can execute any shell command including:
    - Python scripts: "python script.py"
    - UV commands: "uv init project", "uv add torch", "uv run streamlit run app.py"
    - Shell scripts: "bash script.sh"
    - Any CLI tool: "npm install", "docker run", etc.

    Args:
        command: Full command string to execute
        timeout: Maximum execution time in seconds (default: 300 = 5 minutes)
        working_dir: Directory to run command in (default: current directory)

    Returns:
        Tuple of (success: bool, output: str, return_code: int)
        - success: True if command completed with exit code 0
        - output: Combined stdout and stderr output
        - return_code: Command exit code

    Security notes:
        - Uses shell=True for full command flexibility
        - Runs with user's permissions (no sandboxing)
        - User should confirm before execution (handled in CLI)
        - Timeout prevents infinite loops
    """
    try:
        # Validate working directory
        work_path = Path(working_dir)
        if not work_path.exists():
            return False, f"Directory not found: {working_dir}", 1

        # Execute command with timeout
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(work_path)
        )

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            if output:
                output += "\n\n[STDERR]\n"
            output += result.stderr

        # Determine success based on return code
        success = result.returncode == 0

        return success, output if output else "(No output)", result.returncode

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds. Consider increasing timeout or optimizing the command."
        return False, error_msg, -1

    except Exception as e:
        error_msg = f"Error executing command: {str(e)}"
        return False, error_msg, -1


def extract_username_from_hf_whoami(output: str) -> str:
    """
    Extract username from 'hf auth whoami' output.

    Args:
        output: Output from 'hf auth whoami' command

    Returns:
        Username string or "user" if not found

    Example:
        >>> extract_username_from_hf_whoami("username: john\\nemail: john@example.com")
        'john'
    """
    for line in output.split('\n'):
        line = line.strip()
        if line.lower().startswith('username'):
            # Handle formats like "username: john" or "username john"
            parts = line.split(':', 1) if ':' in line else line.split(None, 1)
            if len(parts) > 1:
                return parts[1].strip()
    return "user"


class PerformanceMetrics:
    """
    Track performance metrics for WYN360 CLI sessions.

    Tracks:
    - Response times for each request
    - Tool usage and success rates
    - Error frequency and types
    """

    def __init__(self):
        """Initialize performance metrics tracking."""
        import time

        self.start_time = time.time()
        self.request_times = []  # List of (timestamp, duration_seconds) tuples
        self.tool_calls = {}  # {tool_name: {"success": count, "failed": count}}
        self.errors = []  # List of {"timestamp": ..., "error_type": ..., "message": ...}

    def track_request_time(self, duration: float) -> None:
        """
        Track the duration of a request.

        Args:
            duration: Time taken in seconds
        """
        import time
        self.request_times.append((time.time(), duration))

    def track_tool_call(self, tool_name: str, success: bool) -> None:
        """
        Track a tool call and its success/failure status.

        Args:
            tool_name: Name of the tool that was called
            success: Whether the tool call succeeded
        """
        if tool_name not in self.tool_calls:
            self.tool_calls[tool_name] = {"success": 0, "failed": 0}

        if success:
            self.tool_calls[tool_name]["success"] += 1
        else:
            self.tool_calls[tool_name]["failed"] += 1

    def track_error(self, error_type: str, message: str) -> None:
        """
        Track an error occurrence.

        Args:
            error_type: Type/class of the error
            message: Error message
        """
        import time
        self.errors.append({
            "timestamp": time.time(),
            "error_type": error_type,
            "message": message
        })

    def get_statistics(self) -> Dict[str, any]:
        """
        Calculate and return performance statistics.

        Returns:
            Dictionary containing performance metrics
        """
        import time

        # Response time statistics
        if self.request_times:
            durations = [duration for _, duration in self.request_times]
            avg_response_time = sum(durations) / len(durations)
            min_response_time = min(durations)
            max_response_time = max(durations)
        else:
            avg_response_time = 0.0
            min_response_time = 0.0
            max_response_time = 0.0

        # Tool call statistics
        total_tool_calls = 0
        total_successful_calls = 0
        total_failed_calls = 0

        for tool_name, stats in self.tool_calls.items():
            total_tool_calls += stats["success"] + stats["failed"]
            total_successful_calls += stats["success"]
            total_failed_calls += stats["failed"]

        tool_success_rate = (
            (total_successful_calls / total_tool_calls * 100)
            if total_tool_calls > 0 else 0.0
        )

        # Most used tools (top 5)
        sorted_tools = sorted(
            self.tool_calls.items(),
            key=lambda x: x[1]["success"] + x[1]["failed"],
            reverse=True
        )
        most_used_tools = sorted_tools[:5]

        # Error statistics
        error_count = len(self.errors)
        error_types = {}
        for error in self.errors:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Session duration
        session_duration = time.time() - self.start_time

        return {
            "session_duration_seconds": session_duration,
            "total_requests": len(self.request_times),
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "total_tool_calls": total_tool_calls,
            "successful_tool_calls": total_successful_calls,
            "failed_tool_calls": total_failed_calls,
            "tool_success_rate": tool_success_rate,
            "most_used_tools": most_used_tools,
            "tool_details": self.tool_calls,
            "error_count": error_count,
            "error_types": error_types,
            "errors": self.errors
        }

    def to_dict(self) -> Dict[str, any]:
        """
        Convert metrics to dictionary for serialization.

        Returns:
            Dictionary representation of metrics
        """
        return {
            "start_time": self.start_time,
            "request_times": self.request_times,
            "tool_calls": self.tool_calls,
            "errors": self.errors
        }

    def from_dict(self, data: Dict[str, any]) -> None:
        """
        Load metrics from dictionary.

        Args:
            data: Dictionary containing metrics data
        """
        self.start_time = data.get("start_time", self.start_time)
        self.request_times = data.get("request_times", [])
        self.tool_calls = data.get("tool_calls", {})
        self.errors = data.get("errors", [])
