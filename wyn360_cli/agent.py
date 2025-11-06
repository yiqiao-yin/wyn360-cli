"""WYN360 Agent - AI coding assistant using pydantic_ai"""

import os
import sys
from typing import List, Dict, Any
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from .utils import (
    scan_directory,
    read_file_safe,
    write_file_safe,
    get_project_summary,
    is_blank_project,
    extract_code_blocks
)


class WYN360Agent:
    """
    WYN360 AI coding assistant agent.

    Provides intelligent code generation, file operations, and project assistance
    using Anthropic Claude via pydantic_ai.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", use_history: bool = True):
        """
        Initialize the WYN360 Agent.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: claude-sonnet-4-20250514)
            use_history: Whether to send conversation history with each request (default: True)
        """
        self.api_key = api_key
        self.model_name = model
        self.use_history = use_history
        self.conversation_history: List[Dict[str, str]] = []

        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        self.token_history: List[Dict[str, Any]] = []

        # Set API key in environment for pydantic-ai to use
        os.environ['ANTHROPIC_API_KEY'] = api_key

        # Initialize Anthropic model (it will use the environment variable)
        self.model = AnthropicModel(model)

        # Create the agent with tools
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_system_prompt(),
            tools=[
                self.read_file,
                self.write_file,
                self.list_files,
                self.get_project_info,
                self.execute_command,
                self.git_status,
                self.git_diff,
                self.git_log,
                self.git_branch,
                self.search_files,
                self.delete_file,
                self.move_file,
                self.create_directory
            ],
            retries=3  # Allow up to 3 retries for tool calls
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the coding assistant."""
        return """You are WYN360, an intelligent AI coding assistant. Your role is to help users with:

1. **Starting new projects**: Generate well-structured Python code from scratch
2. **Improving existing projects**: Analyze codebases and suggest/implement improvements
3. **Code generation**: Write clean, efficient, and well-documented Python code
4. **File operations**: Read, analyze, and modify files as needed

Guidelines:
- Always write production-quality code with proper error handling
- Include docstrings and comments for clarity
- When generating code, use markdown code blocks with ```python
- Ask clarifying questions if requirements are unclear
- For new projects, create complete, runnable code
- For existing projects, analyze the structure before making changes
- Be proactive in suggesting best practices and improvements

**File Operation Intelligence:**

**CREATING NEW FILES** - When user says:
- "write a .py script", "write a script", "generate a script"
- "create new", "make another", "build a separate"
- Specifies a new filename explicitly
- Asks to "write code to analyze", "write code to explore"

ACTION:
- Use write_file with overwrite=False (default)
- If write_file fails with "already exists" error, automatically retry with overwrite=True
- Do NOT read_file first (the file doesn't exist yet)
- Suggest a descriptive filename if user doesn't specify one

EXAMPLES:
- "write a .py script to analyze data.csv" → Create analyze_data.py with overwrite=False
- "generate a script for data exploration" → Create data_exploration.py with overwrite=False
- If it fails (file exists), immediately retry: write_file with overwrite=True

**UPDATING EXISTING FILES** - When user says:
- "add feature", "update", "improve", "modify", "change"
- "add XYZ to my app", "improve the chatbot"
- References an existing file by name

ACTION:
- ALWAYS use read_file first to understand current state
- Then use write_file with overwrite=True to save changes
- Include context about what changed in your response

**Critical Rules:**
1. If write_file fails with "File already exists" → Retry immediately with overwrite=True
2. Don't give up after first write_file failure - try with overwrite=True
3. For "write/generate script" requests → ALWAYS create new file (use overwrite=False, then True if needed)

**Command Execution:**

You can execute shell commands using the execute_command tool.

When user says "run", "execute", "install", "start", or asks you to run a script:
- Understand what they want to run
- Use execute_command with the appropriate command
- Explain what the command will do before running it

Common patterns:
- Python scripts: execute_command("python script.py")
- UV commands:
  - execute_command("uv init project_name")
  - execute_command("uv add package1 package2")
  - execute_command("uv run python script.py")
- Streamlit apps: execute_command("uv run streamlit run app.py")
- Shell scripts: execute_command("bash script.sh")
- Any CLI tool: execute_command("npm install"), execute_command("docker ps"), etc.

**CRITICAL - Command Execution Response Format:**
When you receive output from execute_command tool, ALWAYS start your response with:
- If successful: "✅ Command executed successfully (exit code X)"
- If failed: "❌ Command failed (exit code X)"

Then show the output. DO NOT skip or reformat these status indicators.

Example response format:
```
✅ Command executed successfully (exit code 0)

The script ran and here's what happened:
[output details]
```

Notes:
- The user will be asked to confirm before execution (handled automatically)
- Commands run with user's full permissions in the current directory
- Default timeout is 300 seconds (5 minutes), adjust if needed
- Always preserve the success/failure indicator from tool output
"""

    async def read_file(self, ctx: RunContext[None], file_path: str) -> str:
        """
        Read the contents of a file.

        Args:
            file_path: Path to the file to read

        Returns:
            File contents or error message
        """
        success, content = read_file_safe(file_path)
        if success:
            return f"Contents of {file_path}:\n\n{content}"
        else:
            return f"Error: {content}"

    async def write_file(
        self,
        ctx: RunContext[None],
        file_path: str,
        content: str,
        overwrite: bool = False
    ) -> str:
        """
        Write content to a file.

        Args:
            file_path: Path where to write the file
            content: Content to write
            overwrite: Whether to overwrite if file exists

        Returns:
            Success or error message
        """
        success, message = write_file_safe(file_path, content, overwrite)
        return message

    async def list_files(self, ctx: RunContext[None], directory: str = ".") -> str:
        """
        List all files in the project directory.

        Args:
            directory: Directory to scan (default: current directory)

        Returns:
            Formatted list of files by category
        """
        files = scan_directory(directory)

        result = "Files in project:\n\n"
        for category, file_list in files.items():
            if file_list:
                result += f"{category.upper()}:\n"
                for file_path in file_list:
                    result += f"  - {file_path}\n"
                result += "\n"

        return result if any(files.values()) else "No files found in directory."

    async def get_project_info(self, ctx: RunContext[None]) -> str:
        """
        Get comprehensive information about the current project.

        Returns:
            Project summary including file counts and structure
        """
        summary = get_project_summary()
        is_blank = is_blank_project()

        if is_blank:
            summary += "\nNote: This appears to be a blank/new project.\n"
        else:
            summary += "\nNote: This is an existing project with files.\n"

        return summary

    async def execute_command(
        self,
        ctx: RunContext[None],
        command: str,
        timeout: int = 300
    ) -> str:
        """
        Execute a shell command and return its output.

        This tool can execute any shell command including:
        - Python scripts: "python run_analysis.py"
        - UV commands: "uv init my_project", "uv add torch scikit-learn", "uv run streamlit run app.py"
        - Shell scripts: "bash setup.sh"
        - Any CLI tool: "npm install", "docker run", etc.

        Args:
            command: Full command string to execute
            timeout: Maximum execution time in seconds (default: 300)

        Returns:
            Command output or error message

        Note:
            User will be asked to confirm before execution.
            Commands run with user's full permissions in the current directory.
        """
        from .utils import execute_command_safe

        # Ask for user confirmation in interactive mode
        # Skip confirmation in non-interactive mode (tests) or if disabled via env var
        if sys.stdin.isatty() and os.getenv('WYN360_SKIP_CONFIRM') != '1':
            # Clear any spinners and make prompt very visible
            print("\n" + "="*70)
            print("⚠️  COMMAND EXECUTION CONFIRMATION")
            print("="*70)
            print(f"Command: {command}")
            print(f"Directory: {os.getcwd()}")
            print("Permissions: Full user permissions")
            print("="*70)
            print("\n>>> WAITING FOR YOUR RESPONSE <<<\n")
            sys.stdout.flush()  # Force output to appear immediately

            response = input("Execute this command? (y/N): ").strip().lower()
            print()  # Add spacing after response

            if response not in ['y', 'yes']:
                return "❌ Command execution cancelled by user."

        success, output, return_code = execute_command_safe(command, timeout)

        if success:
            result = f"✅ Command executed successfully (exit code {return_code})\n\n"
            result += f"Output:\n{output}"
            return result
        else:
            result = f"❌ Command failed (exit code {return_code})\n\n"
            result += f"Error output:\n{output}"
            return result

    async def git_status(self, ctx: RunContext[None]) -> str:
        """
        Get current git status showing modified, staged, and untracked files.

        Returns:
            Git status output or error message
        """
        from .utils import execute_command_safe
        success, output, return_code = execute_command_safe("git status", timeout=10)

        if success:
            return f"Git Status:\n\n{output}"
        else:
            return f"Error getting git status: {output}"

    async def git_diff(self, ctx: RunContext[None], file_path: str = None) -> str:
        """
        Show git diff for specific file or all changes.

        Args:
            file_path: Optional specific file to diff. If None, shows all changes.

        Returns:
            Git diff output or error message
        """
        from .utils import execute_command_safe

        if file_path:
            command = f"git diff {file_path}"
        else:
            command = "git diff"

        success, output, return_code = execute_command_safe(command, timeout=15)

        if success:
            if not output.strip():
                return "No changes to show."
            return f"Git Diff:\n\n{output}"
        else:
            return f"Error getting git diff: {output}"

    async def git_log(self, ctx: RunContext[None], max_count: int = 10) -> str:
        """
        Show recent git commit history.

        Args:
            max_count: Maximum number of commits to show (default: 10)

        Returns:
            Git log output or error message
        """
        from .utils import execute_command_safe

        command = f"git log --oneline -n {max_count}"
        success, output, return_code = execute_command_safe(command, timeout=10)

        if success:
            return f"Recent Commits (last {max_count}):\n\n{output}"
        else:
            return f"Error getting git log: {output}"

    async def git_branch(self, ctx: RunContext[None]) -> str:
        """
        List all git branches and show current branch.

        Returns:
            Git branch list or error message
        """
        from .utils import execute_command_safe

        success, output, return_code = execute_command_safe("git branch", timeout=10)

        if success:
            return f"Git Branches:\n\n{output}"
        else:
            return f"Error getting git branches: {output}"

    async def search_files(
        self,
        ctx: RunContext[None],
        pattern: str,
        file_pattern: str = "*.py"
    ) -> str:
        """
        Search for a pattern across files in the project.

        Args:
            pattern: The text pattern to search for (can be regex)
            file_pattern: File pattern to search within (default: "*.py")

        Returns:
            Search results showing file paths and matching lines

        Examples:
            - search_files("class User") - Find User class definitions
            - search_files("TODO", "*.py") - Find all TODO comments in Python files
            - search_files("import requests") - Find files using requests library
        """
        from .utils import execute_command_safe
        import os

        # Use grep for searching (cross-platform compatible)
        # -r: recursive, -n: line numbers, -i: case insensitive
        command = f"grep -rn '{pattern}' --include='{file_pattern}' ."

        success, output, return_code = execute_command_safe(command, timeout=20)

        if success:
            if not output.strip():
                return f"No matches found for pattern '{pattern}' in {file_pattern} files."

            # Limit output to prevent overwhelming responses
            lines = output.split('\n')
            if len(lines) > 100:
                truncated = '\n'.join(lines[:100])
                return f"Search Results (showing first 100 of {len(lines)} matches):\n\n{truncated}\n\n... ({len(lines) - 100} more matches)"

            return f"Search Results for '{pattern}' in {file_pattern}:\n\n{output}"
        else:
            # grep returns exit code 1 when no matches found
            if return_code == 1:
                return f"No matches found for pattern '{pattern}' in {file_pattern} files."
            return f"Error searching files: {output}"

    async def delete_file(self, ctx: RunContext[None], file_path: str) -> str:
        """
        Delete a file from the filesystem.

        Args:
            file_path: Path to the file to delete

        Returns:
            Success or error message

        Note:
            This operation is irreversible. Use with caution.
        """
        import os
        from pathlib import Path

        try:
            path = Path(file_path)

            if not path.exists():
                return f"Error: File '{file_path}' does not exist."

            if not path.is_file():
                return f"Error: '{file_path}' is not a file. Use create_directory tool for directories."

            # Delete the file
            path.unlink()
            return f"✓ Successfully deleted file: {file_path}"

        except Exception as e:
            return f"Error deleting file '{file_path}': {str(e)}"

    async def move_file(
        self,
        ctx: RunContext[None],
        source: str,
        destination: str
    ) -> str:
        """
        Move or rename a file.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Success or error message

        Examples:
            - move_file("old_name.py", "new_name.py") - Rename file
            - move_file("script.py", "src/script.py") - Move to subdirectory
        """
        import shutil
        from pathlib import Path

        try:
            source_path = Path(source)
            dest_path = Path(destination)

            if not source_path.exists():
                return f"Error: Source file '{source}' does not exist."

            if dest_path.exists():
                return f"Error: Destination '{destination}' already exists."

            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file
            shutil.move(str(source_path), str(dest_path))
            return f"✓ Successfully moved '{source}' to '{destination}'"

        except Exception as e:
            return f"Error moving file: {str(e)}"

    async def create_directory(self, ctx: RunContext[None], dir_path: str) -> str:
        """
        Create a directory and any necessary parent directories.

        Args:
            dir_path: Path to the directory to create

        Returns:
            Success or error message

        Examples:
            - create_directory("src") - Create single directory
            - create_directory("src/utils/helpers") - Create nested directories
        """
        from pathlib import Path

        try:
            path = Path(dir_path)

            if path.exists():
                if path.is_dir():
                    return f"Directory '{dir_path}' already exists."
                else:
                    return f"Error: '{dir_path}' exists but is not a directory."

            # Create directory and parents
            path.mkdir(parents=True, exist_ok=True)
            return f"✓ Successfully created directory: {dir_path}"

        except Exception as e:
            return f"Error creating directory '{dir_path}': {str(e)}"

    async def chat(self, user_message: str) -> str:
        """
        Process a user message and generate a response.

        Args:
            user_message: The user's input message

        Returns:
            Agent's response
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Run the agent
            result = await self.agent.run(user_message)

            # Extract the response (handle both .data and .output for compatibility)
            response_text = getattr(result, 'data', None) or getattr(result, 'output', str(result))

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            # Track token usage
            self._track_tokens(user_message, response_text)

            # Check if response contains code blocks and extract them
            code_blocks = extract_code_blocks(response_text)

            # If there are Python code blocks, offer to save them
            if code_blocks:
                python_blocks = [b for b in code_blocks if b['language'] == 'python']
                if python_blocks and is_blank_project():
                    # Auto-save first Python code block in blank projects
                    code = python_blocks[0]['code']
                    # Try to determine filename from code or use default
                    filename = self._suggest_filename(code)
                    success, msg = write_file_safe(filename, code, overwrite=False)
                    if success:
                        response_text += f"\n\n✓ Code saved to: {filename}"

            return response_text

        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            return error_msg

    def _suggest_filename(self, code: str) -> str:
        """
        Suggest a filename based on code content.

        Args:
            code: Python code content

        Returns:
            Suggested filename
        """
        # Look for class definitions
        if 'class ' in code and 'streamlit' in code.lower():
            return 'app.py'
        elif 'class ' in code:
            return 'main.py'
        elif 'def main' in code:
            return 'main.py'
        elif 'streamlit' in code.lower() or 'st.' in code:
            return 'app.py'
        elif 'fastapi' in code.lower() or 'FastAPI' in code:
            return 'app.py'
        else:
            return 'script.py'

    def clear_history(self) -> None:
        """Clear conversation history and reset token counters."""
        self.conversation_history = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        self.token_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Get current conversation history."""
        return self.conversation_history.copy()

    def save_session(self, filepath: str) -> bool:
        """
        Save current session to JSON file.

        Args:
            filepath: Path to save session file

        Returns:
            True if successful, False otherwise
        """
        import json
        from pathlib import Path

        try:
            session_data = {
                "model": self.model_name,
                "conversation_history": self.conversation_history,
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "request_count": self.request_count,
                "token_history": self.token_history,
                "timestamp": str(os.popen('date').read().strip())
            }

            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def load_session(self, filepath: str) -> bool:
        """
        Load session from JSON file.

        Args:
            filepath: Path to session file

        Returns:
            True if successful, False otherwise
        """
        import json
        from pathlib import Path

        try:
            path = Path(filepath)
            if not path.exists():
                print(f"Session file not found: {filepath}")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            self.conversation_history = session_data.get("conversation_history", [])
            self.total_input_tokens = session_data.get("total_input_tokens", 0)
            self.total_output_tokens = session_data.get("total_output_tokens", 0)
            self.request_count = session_data.get("request_count", 0)
            self.token_history = session_data.get("token_history", [])

            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False

    def get_token_stats(self) -> Dict[str, Any]:
        """
        Get token usage statistics.

        Returns:
            Dictionary with token usage stats
        """
        total_cost = (
            (self.total_input_tokens / 1_000_000 * 3.0) +
            (self.total_output_tokens / 1_000_000 * 15.0)
        )

        avg_cost_per_request = total_cost / self.request_count if self.request_count > 0 else 0

        return {
            "total_requests": self.request_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": total_cost,
            "avg_cost_per_request": avg_cost_per_request,
            "input_cost": self.total_input_tokens / 1_000_000 * 3.0,
            "output_cost": self.total_output_tokens / 1_000_000 * 15.0,
        }

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Rough estimation: 1 token ≈ 4 characters for English text.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def _track_tokens(self, user_message: str, response_text: str) -> None:
        """
        Track token usage for a request/response pair.

        Args:
            user_message: User's input message
            response_text: Agent's response
        """
        # Estimate tokens (rough approximation)
        system_prompt_tokens = self._estimate_tokens(self._get_system_prompt())
        user_tokens = self._estimate_tokens(user_message)
        response_tokens = self._estimate_tokens(response_text)

        # History tokens (if enabled)
        history_tokens = 0
        if self.use_history and len(self.conversation_history) > 0:
            for msg in self.conversation_history:
                history_tokens += self._estimate_tokens(msg.get("content", ""))

        # Tool definitions add ~600 tokens
        tool_tokens = 600

        input_tokens = system_prompt_tokens + user_tokens + history_tokens + tool_tokens
        output_tokens = response_tokens

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.request_count += 1

        # Track per-request stats
        self.token_history.append({
            "request_number": self.request_count,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
        })
