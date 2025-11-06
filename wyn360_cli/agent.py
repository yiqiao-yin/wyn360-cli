"""WYN360 Agent - AI coding assistant using pydantic_ai"""

import os
import sys
from typing import List, Dict, Any, Optional
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
from .config import WYN360Config


class WYN360Agent:
    """
    WYN360 AI coding assistant agent.

    Provides intelligent code generation, file operations, and project assistance
    using Anthropic Claude via pydantic_ai.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        use_history: bool = True,
        config: Optional[WYN360Config] = None
    ):
        """
        Initialize the WYN360 Agent.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: claude-sonnet-4-20250514)
            use_history: Whether to send conversation history with each request (default: True)
            config: Optional WYN360Config object with user/project configuration
        """
        self.api_key = api_key
        self.config = config

        # Use config model if available, otherwise use provided model
        if config:
            self.model_name = config.model
        else:
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
        self.model = AnthropicModel(self.model_name)

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
            retries=0  # No retries - show errors immediately to model for correction
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the coding assistant."""
        base_prompt = """You are WYN360, an intelligent AI coding assistant. Your role is to help users with:

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
- **KEEP CODE CONCISE** - Write minimal, focused code under 100KB (approximately 800-1000 lines MAX)
- For EDA/analysis scripts: include only essential imports, loading, and 3-5 key visualizations
- For ML models: ONE model type, essential preprocessing, train/evaluate, save model - NO extensive hyperparameter tuning
- If script would be >100KB, break into multiple smaller files (e.g., train_model.py, evaluate_model.py)
- **CRITICAL**: Exceeding size limits causes "exceeded max retries" errors - ALWAYS keep code minimal
- Use write_file with overwrite=False (default)
- If write_file returns an "already exists" error message, call write_file ONCE MORE with overwrite=True
- Do NOT read_file first (the file doesn't exist yet)
- Suggest a descriptive filename if user doesn't specify one
- If tool fails with "exceeded max retries count of 0", the content is likely too large - reduce code size

EXAMPLES:
- "write a .py script to analyze data.csv" → Create analyze_data.py with overwrite=False
- "generate a script for data exploration" → Create data_exploration.py with overwrite=False
- If result is "already exists", then: write_file with overwrite=True ONCE

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

        # Add custom instructions from config if available
        if self.config:
            if self.config.custom_instructions:
                base_prompt += "\n\n**Custom Instructions:**\n"
                base_prompt += self.config.custom_instructions

            # Add project context if available
            if self.config.project_context:
                base_prompt += "\n\n**Project Context:**\n"
                base_prompt += self.config.project_context

            # Add project dependencies info if available
            if self.config.project_dependencies:
                base_prompt += "\n\n**Project Dependencies:**\n"
                base_prompt += "This project uses the following key dependencies:\n"
                for dep in self.config.project_dependencies:
                    base_prompt += f"- {dep}\n"

        return base_prompt

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
        file_path,  # Accept any type, validate manually
        content,    # Accept any type, validate manually
        overwrite: bool = False
    ) -> str:
        """
        Write content to a file.

        IMPORTANT: Keep code concise and under 50KB. For large scripts, break into smaller files.

        Args:
            file_path: Path where to write the file (string)
            content: Content to write (string) - MUST be under 1MB
            overwrite: Whether to overwrite if file exists (boolean, default False)

        Returns:
            Success or error message

        Note: This tool has NO type validation at the framework level to prevent parameter errors.
        All validation happens inside the function with clear error messages.
        """
        try:
            # First, check if content is even a valid type
            if content is None:
                return "Error: content parameter is None. You must provide code content to write."

            # Try to get length - if this fails, content is wrong type
            try:
                content_length = len(content)
            except TypeError as e:
                return f"Error: content must be a string or have length, got type {type(content).__name__}: {str(e)}"

            # Now we know content has a length, check if it's a string
            if not isinstance(content, str):
                # Try to convert to string
                try:
                    content = str(content)
                    content_length = len(content)
                except Exception as e:
                    return f"Error: Cannot convert content to string. Type: {type(content).__name__}, Error: {str(e)}"

            # Validate file_path
            if not file_path:
                return "Error: file_path is required and cannot be empty."

            if not isinstance(file_path, str):
                try:
                    file_path = str(file_path)
                except Exception as e:
                    return f"Error: Cannot convert file_path to string. Type: {type(file_path).__name__}, Error: {str(e)}"

            # Validate content size EARLY (prevent extremely large files)
            max_size = 100_000  # Reduced to 100KB from 1MB
            if content_length > max_size:
                # Truncate and show preview
                preview = content[:500] + f"\n\n... ({content_length - 500} more bytes) ..."
                return f"Error: Content too large ({content_length} bytes, {content_length // 1024}KB). Maximum size is {max_size} bytes ({max_size // 1024}KB).\n\nYour code is too long! Please reduce to under 1000 lines. Break into smaller files if needed.\n\nContent preview:\n{preview}"

            content_preview = content[:100] if content_length > 100 else content

            # Try to write the file
            success, message = write_file_safe(file_path, content, overwrite)

            # If file exists and overwrite is False, provide clear guidance
            if not success and "already exists" in message:
                return f"{message}\n\nNote: If you want to update this file, you must explicitly set overwrite=True in your next write_file call."

            return message
        except TypeError as e:
            return f"TypeError in write_file: {str(e)}. file_path type: {type(file_path)}, content type: {type(content)}, overwrite type: {type(overwrite)}"
        except Exception as e:
            # Log the actual exception for debugging
            import traceback
            tb = traceback.format_exc()
            error_msg = f"Unexpected error in write_file: {type(e).__name__}: {str(e)}\n\nTraceback:\n{tb}"
            return error_msg

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

    async def chat_stream(self, user_message: str):
        """
        Process a user message and stream the response token-by-token.

        NOTE: Due to limitations with streaming and tool execution in pydantic-ai,
        this method falls back to non-streaming when tools are likely needed.

        Args:
            user_message: The user's input message

        Yields:
            Chunks of the response as they're generated
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Use non-streaming for tool execution reliability
            # Streaming in pydantic-ai doesn't work well with tools
            result = await self.agent.run(user_message)

            # Extract the response (handle both .data and .output for compatibility)
            response_text = getattr(result, 'data', None) or getattr(result, 'output', str(result))

            # Simulate streaming by yielding the response in chunks
            chunk_size = 50  # characters per chunk
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[:i+chunk_size]
                yield chunk
                # Small delay to simulate streaming (optional)
                # await asyncio.sleep(0.01)

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
                        save_message = f"\n\n✓ Code saved to: {filename}"
                        yield save_message

        except Exception as e:
            error_msg = f"\n\nAn error occurred: {str(e)}"
            yield error_msg

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

    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different Claude model mid-session.

        Args:
            model_name: Model identifier (haiku, sonnet, opus, or full model ID)

        Returns:
            True if successful, False otherwise

        Supported models:
            - haiku: claude-3-5-haiku-20241022 (fast & cheap)
            - sonnet: claude-sonnet-4-20250514 (balanced, default)
            - opus: claude-opus-4-20250514 (most capable)
        """
        # Model mapping for convenience
        model_map = {
            "haiku": "claude-3-5-haiku-20241022",
            "sonnet": "claude-sonnet-4-20250514",
            "opus": "claude-opus-4-20250514"
        }

        # Resolve model name
        if model_name.lower() in model_map:
            full_model_name = model_map[model_name.lower()]
        else:
            full_model_name = model_name

        try:
            # Create new model instance
            from pydantic_ai.models.anthropic import AnthropicModel
            new_model = AnthropicModel(full_model_name)

            # Update agent with new model
            self.model = new_model
            self.model_name = full_model_name

            # Recreate agent with new model
            from pydantic_ai import Agent
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
                retries=3
            )

            return True
        except Exception as e:
            print(f"Error switching model: {e}")
            return False

    def get_model_info(self) -> dict:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information and pricing
        """
        # Model pricing (per million tokens)
        pricing = {
            "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25, "name": "Haiku"},
            "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00, "name": "Sonnet 4"},
            "claude-opus-4-20250514": {"input": 15.00, "output": 75.00, "name": "Opus 4"}
        }

        model_info = pricing.get(self.model_name, {
            "input": 3.00,
            "output": 15.00,
            "name": "Custom"
        })

        return {
            "current_model": self.model_name,
            "display_name": model_info["name"],
            "input_cost_per_million": model_info["input"],
            "output_cost_per_million": model_info["output"],
            "description": self._get_model_description(self.model_name)
        }

    def _get_model_description(self, model_name: str) -> str:
        """Get description for a model."""
        descriptions = {
            "claude-3-5-haiku-20241022": "Fast & economical - best for simple tasks",
            "claude-sonnet-4-20250514": "Balanced performance - general coding & analysis",
            "claude-opus-4-20250514": "Most capable - complex reasoning & architecture"
        }
        return descriptions.get(model_name, "Custom model")

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
