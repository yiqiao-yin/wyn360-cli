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

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the WYN360 Agent.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: claude-sonnet-4-20250514)
        """
        self.api_key = api_key
        self.model_name = model
        self.conversation_history: List[Dict[str, str]] = []

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
                self.execute_command
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

Notes:
- The user will be asked to confirm before execution (handled automatically)
- Commands run with user's full permissions in the current directory
- Default timeout is 300 seconds (5 minutes), adjust if needed
- Always provide context about expected results
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
