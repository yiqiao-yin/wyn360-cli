"""WYN360 Agent - AI coding assistant using pydantic_ai"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel

# WebSearchTool is optional - only available in newer pydantic-ai versions
try:
    from pydantic_ai import WebSearchTool
    HAS_WEB_SEARCH = True
except ImportError:
    HAS_WEB_SEARCH = False
    WebSearchTool = None

from .utils import (
    scan_directory,
    read_file_safe,
    write_file_safe,
    get_project_summary,
    is_blank_project,
    extract_code_blocks,
    PerformanceMetrics
)
from .config import WYN360Config
from .browser_use import (
    fetch_website_content,
    is_valid_url,
    WebsiteCache,
    HAS_CRAWL4AI
)


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

        # Performance metrics tracking (Phase 10.2)
        self.performance_metrics = PerformanceMetrics()

        # Browser use / website fetching (Phase 12.1, 12.2)
        if config and config.browser_use_cache_enabled and HAS_CRAWL4AI:
            cache_dir = Path.home() / ".wyn360" / "cache" / "fetched_sites"
            self.website_cache = WebsiteCache(
                cache_dir=cache_dir,
                ttl=config.browser_use_cache_ttl,
                max_size_mb=config.browser_use_cache_max_size_mb
            )
        else:
            self.website_cache = None

        # Set API key in environment for pydantic-ai to use
        os.environ['ANTHROPIC_API_KEY'] = api_key

        # Initialize Anthropic model (it will use the environment variable)
        self.model = AnthropicModel(self.model_name)

        # Create the agent with tools and web search
        # WebSearchTool is now enabled with pydantic-ai >= 1.13.0
        builtin_tools = []
        if HAS_WEB_SEARCH:
            # Enable web search with max 5 uses per session
            builtin_tools.append(WebSearchTool(max_uses=5))

        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_system_prompt(),
            builtin_tools=builtin_tools,
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
                self.create_directory,
                # HuggingFace tools
                self.check_hf_authentication,
                self.authenticate_hf,
                self.create_hf_readme,
                self.create_hf_space,
                self.push_to_hf_space,
                # GitHub tools (Phase 8.1)
                self.check_gh_authentication,
                self.authenticate_gh,
                self.gh_commit_changes,
                self.gh_create_pr,
                self.gh_create_branch,
                self.gh_checkout_branch,
                self.gh_merge_branch,
                # Test Generation tool
                self.generate_tests,
                # Browser use / website fetching (Phase 12.1, 12.2, 12.3)
                self.fetch_website,
                self.clear_website_cache,
                self.show_cache_stats
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

**HuggingFace Integration (Phase 2 - Full Deployment):**

You can help users deploy apps to HuggingFace Spaces automatically!

**Complete Workflow when user says "push to huggingface" or "deploy to HF":**

1. **Check Authentication (ONLY ONCE per session)**:
   - Call check_hf_authentication() ONE TIME only
   - If it returns "✓ Authenticated", NEVER check again - remember they're authenticated
   - If not authenticated, ask for token and use authenticate_hf(token)
   - Once authenticated, proceed to step 2

2. **Gather Information (if not already provided)**:
   - Space name in format "username/repo-name" (e.g., "eagle0504/test-echo-bot")
   - App title for the Space
   - SDK type (streamlit, gradio, docker, or static)
   - App directory path (where app.py and requirements.txt are located)

3. **Deploy to HuggingFace (Automatic)**:
   a. Navigate to the app directory if needed
   b. Create README.md with create_hf_readme(title, sdk):
      - For Streamlit: sdk="streamlit", app_file="app.py"
      - For Gradio: sdk="gradio", app_file="app.py"
   c. Create Space with create_hf_space(space_name, sdk):
      - Returns Space URL or "already exists" message
   d. Upload files with push_to_hf_space(space_name, directory):
      - Uploads all files in directory to the Space
      - Returns live Space URL

4. **Completion**:
   - Confirm files were uploaded successfully
   - Provide the live Space URL: https://huggingface.co/spaces/{space_name}
   - Tell user "🎉 Your app is live!"

**CRITICAL - Avoid Authentication Loops:**
- Do NOT call check_hf_authentication() multiple times in one conversation
- Once user is authenticated, trust it and proceed
- If user provided token in previous messages, they are authenticated - don't ask again
- If user gave you all details (token, space name, title, directory), proceed directly to deployment

**Important Notes:**
- Space names MUST be in "username/repo-name" format (e.g., "eagle0504/test-echo-bot")
- README.md needs proper YAML frontmatter for Spaces to work
- For Streamlit: typically need app.py and requirements.txt in same directory
- The entire directory gets uploaded, so make sure only necessary files are included
- If Space already exists, files will be updated (not replaced)

**Test Generation (Phase 7.2):**

You can automatically generate unit tests for Python files!

**When to use generate_tests:**
- User asks "generate tests for [file]"
- User says "create test file for [file]"
- User wants pytest tests for their code

**Workflow:**
1. Confirm the Python file path with user
2. Use generate_tests(file_path) to analyze and generate tests
3. Explain what was generated (functions, classes covered)
4. Remind user that generated tests are templates with TODO markers
5. Suggest they fill in actual test logic and assertions

**What it does:**
- Parses Python file using AST (safe, doesn't execute code)
- Finds all public functions and classes
- Generates pytest test stubs with docstrings
- Creates test_{filename}.py file
- Includes TODO comments for user to fill in

**Important:**
- Generated tests are TEMPLATES - they have pass statements and TODO comments
- User must add actual test logic and assertions
- Tests won't fail initially - they need implementation
- Good starting point to save time on test structure

**GitHub Integration (Phase 8.1):**

You can help users manage their GitHub repositories directly!

**Complete Workflow when user says "commit to github" or "create PR" or "manage branches":**

1. **Check Authentication (ONLY ONCE per session)**:
   - Call check_gh_authentication() ONE TIME only
   - If it returns "✓ Authenticated", NEVER check again - remember they're authenticated
   - If not authenticated, ask for token and use authenticate_gh(token)
   - Once authenticated, proceed to step 2

2. **Available GitHub Operations:**

   **Committing Changes:**
   - When user says "commit changes" or "push to github":
     a. Check authentication status
     b. Use gh_commit_changes(message, push=True) to commit and push
     c. Confirm success with commit message and branch info

   **Creating Pull Requests:**
   - When user says "create PR" or "open pull request":
     a. Verify authentication
     b. Ensure you're on a feature branch (not main)
     c. Use gh_create_pr(title, body, base_branch)
     d. Return PR URL

   **Managing Branches:**
   - Create branch: gh_create_branch(branch_name, checkout=True)
   - Switch branch: gh_checkout_branch(branch_name)
   - Merge branches: gh_merge_branch(source_branch, target_branch)

3. **Important Notes:**
   - Always check for uncommitted changes before branch operations
   - Commit changes automatically stage all files with 'git add -A'
   - PR creation requires being on a feature branch (not main)
   - GitHub token needs 'repo' and 'workflow' scopes
   - All git commands use execute_command_safe with user confirmation

**CRITICAL - Avoid Authentication Loops:**
- Do NOT call check_gh_authentication() multiple times in one conversation
- Once user is authenticated, trust it and proceed
- If user provided token in previous messages, they are authenticated - don't ask again

**Common Use Cases:**

Use Case 1: Commit and Push
```
User: The codebase is good. Commit to github.
You: [Check auth] → gh_commit_changes("Update codebase", push=True)
```

Use Case 2: Create Pull Request
```
User: Create a PR for these changes
You: [Check auth] → [Verify on feature branch] → gh_create_pr("Add feature", "Description")
```

Use Case 3: Branch Management
```
User: Create a new branch called feature/auth
You: gh_create_branch("feature/auth", checkout=True)
```

Use Case 4: Merge Branches
```
User: Merge feature/auth into main
You: gh_merge_branch("feature/auth", "main")
```

**Web Capabilities (Phase 11.1 + 12.1):**

You now have TWO tools for web access:
1. **WebSearchTool** - For searching the web (limited to 5 uses)
2. **fetch_website** - For fetching specific URLs directly (Phase 12.1)

**CRITICAL - When to use each tool:**

**Use fetch_website() when:**
- User provides a SPECIFIC URL: "Read https://github.com/user/repo"
- User wants content from an exact webpage: "What's on https://example.com"
- User says "fetch", "read", "get", or "load" with a URL
- Examples:
  - ✅ "Read https://github.com/britbrat0/cs676" → fetch_website()
  - ✅ "What's on https://python.org/downloads" → fetch_website()
  - ✅ "Fetch https://docs.anthropic.com" → fetch_website()
  - ✅ "Load the content from https://example.com" → fetch_website()

**Use WebSearchTool when:**
- User asks to FIND or SEARCH for something (no specific URL)
- User asks about weather, current events, or general queries
- User wants recommendations or lists of resources
- Examples:
  - ✅ "Find a popular GitHub repo for machine learning" → WebSearchTool
  - ✅ "What's the weather in New York?" → WebSearchTool
  - ✅ "What are good Python libraries for data visualization?" → WebSearchTool
  - ✅ "Find tutorials for FastAPI" → WebSearchTool
  - ✅ "What's new in Python 3.13?" → WebSearchTool

**fetch_website Details:**
- Fetches full DOM content from the URL
- Converts to LLM-friendly markdown
- Smart truncation to stay under token limits
- Cached for 30 minutes (configurable)
- Returns: Full page content, structure preserved
- Max tokens: 50,000 (configurable via config)

**WebSearchTool Details:**
- Searches the web and returns top results
- Limited to 5 searches per session
- Returns: Search results with snippets
- Use when you need to FIND something, not fetch a specific URL

**CITATION FORMAT:**
Always include:
- Source URL
- Relevant excerpt or summary
- Publication date/last updated (if available)

Example:
```
According to [Source Name](URL):
"[Relevant excerpt]"
(Last updated: YYYY-MM-DD)
```

**AVOID WEB TOOLS FOR:**
- Code generation (use your training data)
- File operations (use read_file, write_file)
- Local project queries (use list_files, get_project_info)
- Git operations (use git_status, git_diff, git_log)
- General programming concepts you already know

**COST AWARENESS:**
- Web search costs $10 per 1,000 searches + token costs
- fetch_website uses tokens but no search cost
- Use judiciously - only when truly needed for current/live information

**Decision Tree:**
```
User mentions URL? (https://...)
  → YES: Use fetch_website()
  → NO: Does user want to FIND/SEARCH something?
    → YES: Use WebSearchTool
    → NO: Don't use web tools
```

**Complete Examples:**
- ✅ "Read https://github.com/britbrat0/cs676" → fetch_website()
- ✅ "What's on https://python.org/downloads" → fetch_website()
- ✅ "Fetch https://docs.anthropic.com/api" → fetch_website()
- ✅ "What's the weather in San Francisco?" → WebSearchTool
- ✅ "Find a popular GitHub repo for machine learning" → WebSearchTool
- ✅ "What are the latest security vulnerabilities in Node.js?" → WebSearchTool
- ✅ "Show me good Python data science libraries" → WebSearchTool
- ❌ "Write a FastAPI app" → Don't use web tools (use training data)
- ❌ "Show me the files in this project" → Don't use web tools (use list_files)
- ❌ "What's git?" → Don't use web tools (you know this)
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

        # Track tool call
        self.performance_metrics.track_tool_call("read_file", success)

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

            # Track tool call
            self.performance_metrics.track_tool_call("write_file", success)

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

        # Track tool call (list_files always succeeds)
        self.performance_metrics.track_tool_call("list_files", True)

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

            # Confirm user's input
            if response in ['y', 'yes']:
                print("✓ Confirmed. Executing command...\n")
                sys.stdout.flush()
            else:
                print(f"✗ Cancelled (pressed '{response or 'N'}').\n")
                sys.stdout.flush()
                return "❌ Command execution cancelled by user."

        success, output, return_code = execute_command_safe(command, timeout)

        # Track tool call
        self.performance_metrics.track_tool_call("execute_command", success)

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

        # Track tool call
        self.performance_metrics.track_tool_call("git_status", success)

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

        # Track tool call (grep returns 1 for no matches, which is not really a failure)
        tool_success = success or return_code == 1
        self.performance_metrics.track_tool_call("search_files", tool_success)

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

    # ==================== HuggingFace Integration Tools ====================

    async def check_hf_authentication(self, ctx: RunContext[None]) -> str:
        """
        Check if user is authenticated with HuggingFace.

        Returns authentication status and username if authenticated.

        Examples:
            - "check if I'm logged into huggingface"
            - "am I authenticated with HF?"
        """
        from .utils import execute_command_safe, extract_username_from_hf_whoami

        # Check environment variable
        hf_token = os.getenv('HF_TOKEN')

        # Try hf CLI whoami
        success, output, code = execute_command_safe("hf auth whoami", timeout=10)

        if success and "username" in output.lower():
            username = extract_username_from_hf_whoami(output)
            return f"✓ Authenticated with HuggingFace as '{username}'"
        elif hf_token:
            # Token exists but CLI not authenticated - try to authenticate automatically
            os.environ['HF_TOKEN'] = hf_token
            success2, output2, code2 = execute_command_safe(
                "hf auth login --token $HF_TOKEN",
                timeout=30
            )
            if success2 or "token is valid" in output2.lower():
                success3, output3, _ = execute_command_safe("hf auth whoami", timeout=10)
                username = extract_username_from_hf_whoami(output3) if success3 else "user"
                return f"✓ Authenticated with HuggingFace as '{username}' (auto-authenticated using HF_TOKEN from environment)"
            else:
                return f"❌ HF_TOKEN found in environment but authentication failed. Error: {output2[:200]}"
        else:
            return ("Not authenticated with HuggingFace. To push code to HuggingFace Spaces, I need your access token.\n\n"
                   "You can get a token from: https://huggingface.co/settings/tokens\n\n"
                   "Then either:\n"
                   "1. Export it before starting: export HF_TOKEN=your_token\n"
                   "2. Provide it to me in chat and I'll authenticate you")

    async def authenticate_hf(self, ctx: RunContext[None], token: str) -> str:
        """
        Authenticate with HuggingFace using provided token.

        Args:
            token: HuggingFace access token (starts with 'hf_')

        Returns:
            Status message with username if successful

        Examples:
            - "authenticate with HF using token hf_xxxxx"
            - "login to huggingface with hf_xxxxx"
        """
        from .utils import execute_command_safe, extract_username_from_hf_whoami

        # Validate token format
        if not token or len(token) < 10:
            return "❌ Invalid token format. HuggingFace tokens should be longer."

        # Save token to environment for this session
        os.environ['HF_TOKEN'] = token

        # Authenticate via CLI using the token environment variable
        success, output, code = execute_command_safe(
            "hf auth login --token $HF_TOKEN",
            timeout=30
        )

        if success or "token is valid" in output.lower():
            # Get username
            success2, output2, _ = execute_command_safe("hf auth whoami", timeout=10)
            username = extract_username_from_hf_whoami(output2) if success2 else "user"
            return f"✓ Successfully authenticated with HuggingFace as '{username}'\n\nYou can now push code to Spaces!"
        else:
            return f"❌ Authentication failed. Please check your token.\n\nError: {output[:200]}"

    async def create_hf_readme(
        self,
        ctx: RunContext[None],
        title: str,
        sdk: str = "streamlit",
        sdk_version: str = "1.34.0",
        app_file: str = "app.py",
        emoji: str = "🔥",
        color_from: str = "indigo",
        color_to: str = "green",
        license: str = "mit"
    ) -> str:
        """
        Generate README.md with HuggingFace Space frontmatter.

        Args:
            title: Space title
            sdk: SDK type (streamlit, gradio, docker, static)
            sdk_version: SDK version
            app_file: Main app file (app.py or Home.py for streamlit)
            emoji: Space emoji
            color_from: Gradient start color
            color_to: Gradient end color
            license: License type

        Returns:
            Path to created README.md

        Examples:
            - "create a README for my streamlit app called 'Echo Bot'"
            - "generate huggingface README with title 'Data Viz'"
        """
        from .utils import write_file_safe

        readme_content = f"""---
title: {title}
emoji: {emoji}
colorFrom: {color_from}
colorTo: {color_to}
sdk: {sdk}
sdk_version: {sdk_version}
app_file: {app_file}
pinned: false
license: {license}
---

# {title}

This Space was created with WYN360-CLI.

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
"""

        # Write README.md
        success, msg = write_file_safe("README.md", readme_content, overwrite=True)

        if success:
            return f"✓ Created README.md with {sdk} Space configuration (title: {title})"
        else:
            return f"❌ Failed to create README.md: {msg}"

    async def create_hf_space(
        self,
        ctx: RunContext[None],
        space_name: str,
        sdk: str = "streamlit",
        private: bool = False
    ) -> str:
        """
        Create a HuggingFace Space repository.

        Args:
            space_name: Space name in format "username/repo-name" (e.g., "eagle0504/test-echo-bot")
            sdk: SDK type (streamlit, gradio, docker, static)
            private: Whether the Space should be private (default: False)

        Returns:
            Success message with Space URL or error message

        Examples:
            - "create huggingface space eagle0504/my-app with streamlit"
            - "create private space myuser/secret-app"
        """
        from .utils import execute_command_safe

        # Validate space name format
        if '/' not in space_name:
            return f"❌ Invalid space name format. Must be 'username/repo-name' (e.g., 'eagle0504/test-echo-bot'), got: {space_name}"

        # Build command
        cmd = f"hf repo create {space_name} --type=space --space-sdk={sdk}"
        if private:
            cmd += " --private"

        # Execute command
        success, output, code = execute_command_safe(cmd, timeout=60)

        if success or "already exists" in output.lower():
            space_url = f"https://huggingface.co/spaces/{space_name}"
            if "already exists" in output.lower():
                return f"✓ Space '{space_name}' already exists at {space_url}"
            else:
                return f"✓ Successfully created Space '{space_name}' at {space_url}"
        else:
            return f"❌ Failed to create Space '{space_name}'\n\nError: {output[:300]}"

    async def push_to_hf_space(
        self,
        ctx: RunContext[None],
        space_name: str,
        directory: str = "."
    ) -> str:
        """
        Upload files to HuggingFace Space.

        Args:
            space_name: Space name in format "username/repo-name"
            directory: Directory to upload (default: current directory)

        Returns:
            Success message or error message

        Examples:
            - "push current directory to eagle0504/test-echo-bot"
            - "upload test_echo folder to myuser/my-app"
        """
        from .utils import execute_command_safe
        from pathlib import Path

        # Validate space name format
        if '/' not in space_name:
            return f"❌ Invalid space name format. Must be 'username/repo-name', got: {space_name}"

        # Validate directory exists
        dir_path = Path(directory)
        if not dir_path.exists():
            return f"❌ Directory not found: {directory}"

        # Check for required files
        app_files = list(dir_path.glob("app.py")) + list(dir_path.glob("Home.py"))
        if not app_files:
            return f"⚠️  Warning: No app.py or Home.py found in {directory}. Make sure this is the correct directory."

        # Upload entire directory to Space
        cmd = f"hf upload {space_name} {directory} . --repo-type=space"

        # Execute upload
        success, output, code = execute_command_safe(cmd, timeout=300)

        if success:
            space_url = f"https://huggingface.co/spaces/{space_name}"
            return f"✓ Successfully uploaded files to Space '{space_name}'\n\n🎉 Your app is live at: {space_url}"
        else:
            # Check if it's a quota/permission error
            if "quota" in output.lower() or "limit" in output.lower():
                return f"❌ Upload failed: You may have reached your HuggingFace storage quota.\n\nError: {output[:300]}"
            elif "not found" in output.lower() or "doesn't exist" in output.lower():
                return f"❌ Upload failed: Space '{space_name}' doesn't exist. Create it first with create_hf_space.\n\nError: {output[:300]}"
            else:
                return f"❌ Upload failed for Space '{space_name}'\n\nError: {output[:300]}"

    # ==================== GitHub Integration Tools (Phase 8.1) ====================

    async def check_gh_authentication(self, ctx: RunContext[None]) -> str:
        """
        Check if user is authenticated with GitHub.

        Returns authentication status and username if authenticated.

        Examples:
            - "check if I'm logged into github"
            - "am I authenticated with GitHub?"
        """
        from .utils import execute_command_safe

        # Check environment variable
        gh_token = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')

        # Try gh CLI auth status
        success, output, code = execute_command_safe("gh auth status", timeout=10)

        if success and ("logged in" in output.lower() or "authenticated" in output.lower()):
            # Extract username from output
            lines = output.split('\n')
            username = "user"
            for line in lines:
                if "account" in line.lower() or "logged in" in line.lower():
                    # Try to extract username
                    parts = line.split()
                    if len(parts) >= 2:
                        username = parts[-1].strip('()')
                        break
            return f"✓ Authenticated with GitHub as '{username}'"
        elif gh_token:
            # Token exists but CLI not authenticated - try to authenticate automatically
            os.environ['GH_TOKEN'] = gh_token
            success2, output2, code2 = execute_command_safe(
                f"echo '{gh_token}' | gh auth login --with-token",
                timeout=30
            )
            if success2 or "authenticated" in output2.lower():
                success3, output3, _ = execute_command_safe("gh auth status", timeout=10)
                return f"✓ Authenticated with GitHub (auto-authenticated using GH_TOKEN from environment)"
            else:
                return f"❌ GH_TOKEN found in environment but authentication failed. Error: {output2[:200]}"
        else:
            return ("Not authenticated with GitHub. To use GitHub features, I need your access token.\n\n"
                   "You can create a token from: https://github.com/settings/tokens\n"
                   "Required scopes: repo, workflow\n\n"
                   "Then either:\n"
                   "1. Export it before starting: export GH_TOKEN=your_token\n"
                   "2. Provide it to me in chat and I'll authenticate you")

    async def authenticate_gh(self, ctx: RunContext[None], token: str) -> str:
        """
        Authenticate with GitHub using provided token.

        Args:
            token: GitHub personal access token (starts with 'ghp_' or 'github_pat_')

        Returns:
            Status message with username if successful

        Examples:
            - "authenticate with github using token ghp_xxxxx"
            - "login to github with this token: ghp_xxxxx"
        """
        from .utils import execute_command_safe

        # Validate token format
        if not (token.startswith('ghp_') or token.startswith('github_pat_')):
            return "❌ Invalid token format. GitHub tokens start with 'ghp_' or 'github_pat_'"

        # Store in environment
        os.environ['GH_TOKEN'] = token

        # Authenticate using gh CLI
        success, output, code = execute_command_safe(
            f"echo '{token}' | gh auth login --with-token",
            timeout=30
        )

        if success or "authenticated" in output.lower():
            # Verify authentication
            success2, output2, _ = execute_command_safe("gh auth status", timeout=10)
            if success2:
                return "✓ Successfully authenticated with GitHub!\n\nYou can now use GitHub features like committing, creating PRs, and managing branches."
            else:
                return "✓ Token accepted, but unable to verify authentication status. You may need to run 'gh auth status' manually."
        else:
            return f"❌ Authentication failed: {output[:300]}\n\nPlease check your token and try again."

    async def gh_commit_changes(
        self,
        ctx: RunContext[None],
        message: str,
        push: bool = True
    ) -> str:
        """
        Commit changes to the current Git repository and optionally push to GitHub.

        Args:
            message: Commit message
            push: Whether to push to remote (default: True)

        Returns:
            Status message

        Examples:
            - "commit these changes with message 'Add authentication'"
            - "commit and push with message 'Fix bug in API'"
        """
        from .utils import execute_command_safe

        # Check if we're in a git repo
        success, output, _ = execute_command_safe("git rev-parse --git-dir", timeout=5)
        if not success:
            return "❌ Not a git repository. Initialize with 'git init' first."

        # Check for changes
        success, output, _ = execute_command_safe("git status --porcelain", timeout=5)
        if not success or not output.strip():
            return "No changes to commit. Working tree is clean."

        # Add all changes
        success, output, _ = execute_command_safe("git add -A", timeout=10)
        if not success:
            return f"❌ Failed to stage changes: {output[:200]}"

        # Commit changes
        commit_cmd = f"git commit -m \"{message}\""
        success, output, code = execute_command_safe(commit_cmd, timeout=30)

        if not success and code != 0:
            if "nothing to commit" in output.lower():
                return "No changes to commit. All files are already staged."
            return f"❌ Commit failed: {output[:300]}"

        result = f"✓ Successfully committed changes\nMessage: {message}\n"

        # Push to remote if requested
        if push:
            # Check if remote exists
            success, output, _ = execute_command_safe("git remote -v", timeout=5)
            if not success or not output.strip():
                return result + "\n⚠️  No remote repository configured. Changes committed locally only."

            # Get current branch
            success, branch_output, _ = execute_command_safe("git branch --show-current", timeout=5)
            current_branch = branch_output.strip() if success else "main"

            # Push to remote
            push_cmd = f"git push origin {current_branch}"
            success, push_output, _ = execute_command_safe(push_cmd, timeout=60)

            if success:
                result += f"\n✓ Successfully pushed to remote branch '{current_branch}'"
            else:
                if "no upstream branch" in push_output.lower():
                    result += f"\n⚠️  No upstream branch set. Try: git push -u origin {current_branch}"
                else:
                    result += f"\n❌ Push failed: {push_output[:200]}"

        return result

    async def gh_create_pr(
        self,
        ctx: RunContext[None],
        title: str,
        body: str = "",
        base_branch: str = "main"
    ) -> str:
        """
        Create a pull request on GitHub.

        Args:
            title: PR title
            body: PR description (optional)
            base_branch: Target branch (default: "main")

        Returns:
            PR URL or error message

        Examples:
            - "create PR with title 'Add authentication feature'"
            - "open pull request to main with title 'Fix bug' and description 'Fixes issue #123'"
        """
        from .utils import execute_command_safe

        # Check authentication
        success, output, _ = execute_command_safe("gh auth status", timeout=10)
        if not success:
            return "❌ Not authenticated with GitHub. Please authenticate first."

        # Get current branch
        success, branch_output, _ = execute_command_safe("git branch --show-current", timeout=5)
        if not success:
            return "❌ Not in a git repository or unable to determine current branch."

        current_branch = branch_output.strip()
        if current_branch == base_branch:
            return f"❌ Cannot create PR from '{current_branch}' to itself. Please switch to a feature branch."

        # Build gh pr create command
        cmd_parts = [
            "gh pr create",
            f"--title \"{title}\"",
            f"--base {base_branch}"
        ]

        if body:
            cmd_parts.append(f"--body \"{body}\"")
        else:
            cmd_parts.append("--body \"\"")

        cmd = " ".join(cmd_parts)

        # Create PR
        success, output, code = execute_command_safe(cmd, timeout=30)

        if success:
            # Extract PR URL from output
            lines = output.split('\n')
            pr_url = ""
            for line in lines:
                if "https://github.com" in line and "/pull/" in line:
                    pr_url = line.strip()
                    break

            if pr_url:
                return f"✓ Successfully created pull request!\n\n{pr_url}\n\nTitle: {title}"
            else:
                return f"✓ Pull request created successfully!\n\n{output[:300]}"
        else:
            if "already exists" in output.lower():
                return f"❌ A pull request already exists for branch '{current_branch}'"
            elif "no commits" in output.lower():
                return f"❌ No commits to create PR. The branches are identical."
            else:
                return f"❌ Failed to create pull request: {output[:300]}"

    async def gh_create_branch(
        self,
        ctx: RunContext[None],
        branch_name: str,
        checkout: bool = True
    ) -> str:
        """
        Create a new Git branch.

        Args:
            branch_name: Name for the new branch
            checkout: Whether to switch to the new branch (default: True)

        Returns:
            Status message

        Examples:
            - "create a new branch called feature/authentication"
            - "create branch bugfix/api-error and switch to it"
        """
        from .utils import execute_command_safe

        # Validate branch name
        if not branch_name or ' ' in branch_name:
            return f"❌ Invalid branch name: '{branch_name}'. Branch names cannot contain spaces."

        # Check if we're in a git repo
        success, output, _ = execute_command_safe("git rev-parse --git-dir", timeout=5)
        if not success:
            return "❌ Not a git repository. Initialize with 'git init' first."

        # Check if branch already exists
        success, output, _ = execute_command_safe(f"git rev-parse --verify {branch_name}", timeout=5)
        if success:
            return f"❌ Branch '{branch_name}' already exists. Use gh_checkout_branch to switch to it."

        # Create branch
        if checkout:
            cmd = f"git checkout -b {branch_name}"
        else:
            cmd = f"git branch {branch_name}"

        success, output, code = execute_command_safe(cmd, timeout=10)

        if success:
            if checkout:
                return f"✓ Created and switched to new branch '{branch_name}'"
            else:
                return f"✓ Created new branch '{branch_name}'"
        else:
            return f"❌ Failed to create branch: {output[:200]}"

    async def gh_checkout_branch(
        self,
        ctx: RunContext[None],
        branch_name: str
    ) -> str:
        """
        Switch to an existing Git branch.

        Args:
            branch_name: Name of the branch to switch to

        Returns:
            Status message

        Examples:
            - "checkout branch main"
            - "switch to branch feature/authentication"
        """
        from .utils import execute_command_safe

        # Check if we're in a git repo
        success, output, _ = execute_command_safe("git rev-parse --git-dir", timeout=5)
        if not success:
            return "❌ Not a git repository."

        # Get current branch
        success, current_output, _ = execute_command_safe("git branch --show-current", timeout=5)
        current_branch = current_output.strip() if success else ""

        if current_branch == branch_name:
            return f"Already on branch '{branch_name}'"

        # Check for uncommitted changes
        success, status_output, _ = execute_command_safe("git status --porcelain", timeout=5)
        if success and status_output.strip():
            return f"⚠️  You have uncommitted changes. Please commit or stash them before switching branches."

        # Checkout branch
        cmd = f"git checkout {branch_name}"
        success, output, code = execute_command_safe(cmd, timeout=10)

        if success:
            return f"✓ Switched to branch '{branch_name}'"
        else:
            if "did not match any file" in output.lower() or "unknown revision" in output.lower():
                return f"❌ Branch '{branch_name}' does not exist. Use gh_create_branch to create it."
            else:
                return f"❌ Failed to checkout branch: {output[:200]}"

    async def gh_merge_branch(
        self,
        ctx: RunContext[None],
        source_branch: str,
        target_branch: str = None
    ) -> str:
        """
        Merge one branch into another.

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into (default: current branch)

        Returns:
            Status message

        Examples:
            - "merge feature/authentication into main"
            - "merge branch develop into current branch"
        """
        from .utils import execute_command_safe

        # Check if we're in a git repo
        success, output, _ = execute_command_safe("git rev-parse --git-dir", timeout=5)
        if not success:
            return "❌ Not a git repository."

        # Get current branch if target not specified
        success, current_output, _ = execute_command_safe("git branch --show-current", timeout=5)
        current_branch = current_output.strip() if success else ""

        if target_branch is None:
            target_branch = current_branch
        else:
            # Switch to target branch if not already there
            if current_branch != target_branch:
                switch_success, switch_output, _ = execute_command_safe(
                    f"git checkout {target_branch}",
                    timeout=10
                )
                if not switch_success:
                    return f"❌ Failed to switch to target branch '{target_branch}': {switch_output[:200]}"

        # Check for uncommitted changes
        success, status_output, _ = execute_command_safe("git status --porcelain", timeout=5)
        if success and status_output.strip():
            return f"⚠️  You have uncommitted changes. Please commit or stash them before merging."

        # Merge branches
        cmd = f"git merge {source_branch}"
        success, output, code = execute_command_safe(cmd, timeout=30)

        if success:
            if "already up to date" in output.lower():
                return f"Branch '{target_branch}' is already up to date with '{source_branch}'"
            elif "fast-forward" in output.lower():
                return f"✓ Successfully merged '{source_branch}' into '{target_branch}' (fast-forward)"
            else:
                return f"✓ Successfully merged '{source_branch}' into '{target_branch}'"
        else:
            if "conflict" in output.lower():
                return f"❌ Merge conflict detected! Please resolve conflicts manually:\n{output[:300]}"
            elif "not something we can merge" in output.lower():
                return f"❌ Branch '{source_branch}' does not exist."
            else:
                return f"❌ Merge failed: {output[:300]}"

    # ==================== Test Generation Tool ====================

    async def generate_tests(
        self,
        ctx: RunContext[None],
        file_path: str,
        test_file_path: str = None
    ) -> str:
        """
        Generate unit tests for a Python file.

        Analyzes the Python file and creates pytest test cases for functions and classes.

        Args:
            file_path: Path to Python file to generate tests for
            test_file_path: Optional path for test file (default: test_{filename}.py)

        Returns:
            Success message with test file path or error message

        Examples:
            - "generate tests for calculator.py"
            - "create tests for utils/helpers.py"
        """
        import ast
        from pathlib import Path
        from .utils import read_file_safe, write_file_safe

        # Validate file exists
        file_p = Path(file_path)
        if not file_p.exists():
            return f"❌ File not found: {file_path}"

        if not file_p.suffix == '.py':
            return f"❌ File must be a Python file (.py), got: {file_p.suffix}"

        # Read the file
        success, content = read_file_safe(str(file_p))
        if not success:
            return f"❌ Failed to read file: {content}"

        # Parse the Python code
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return f"❌ Syntax error in {file_path}: {str(e)}"

        # Extract functions and classes
        functions = []
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions and methods inside classes
                if not node.name.startswith('_'):
                    # Check if it's a module-level function
                    parent_is_module = any(
                        isinstance(parent, ast.Module)
                        for parent in ast.walk(tree)
                        if hasattr(parent, 'body') and node in getattr(parent, 'body', [])
                    )
                    if parent_is_module or node.col_offset == 0:
                        functions.append({
                            'name': node.name,
                            'args': [arg.arg for arg in node.args.args if arg.arg != 'self'],
                            'lineno': node.lineno
                        })
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    methods = [
                        n.name for n in node.body
                        if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')
                    ]
                    classes.append({
                        'name': node.name,
                        'methods': methods,
                        'lineno': node.lineno
                    })

        if not functions and not classes:
            return f"⚠️  No testable functions or classes found in {file_path}"

        # Determine test file path
        if test_file_path is None:
            test_file_path = file_p.parent / f"test_{file_p.name}"
        else:
            test_file_path = Path(test_file_path)

        # Generate test code
        module_name = file_p.stem
        test_code = f'''"""Unit tests for {module_name}.py"""

import pytest
from {module_name} import {', '.join([f['name'] for f in functions] + [c['name'] for c in classes])}


'''

        # Generate test functions
        for func in functions:
            test_code += f'''def test_{func['name']}_basic():
    """Test {func['name']} with basic inputs"""
    # TODO: Add test implementation
    # Example: result = {func['name']}({', '.join(['arg' + str(i+1) for i in range(len(func['args']))])})
    # assert result == expected_value
    pass


'''

        # Generate test classes
        for cls in classes:
            test_code += f'''class Test{cls['name']}:
    """Tests for {cls['name']} class"""

    def test_initialization(self):
        """Test {cls['name']} initialization"""
        # TODO: Add test implementation
        # obj = {cls['name']}()
        # assert obj is not None
        pass

'''
            for method in cls['methods'][:3]:  # Limit to first 3 methods
                test_code += f'''    def test_{method}(self):
        """Test {cls['name']}.{method}() method"""
        # TODO: Add test implementation
        pass

'''

        # Write test file
        success, msg = write_file_safe(str(test_file_path), test_code, overwrite=False)

        if success:
            summary = f"✓ Generated test file: {test_file_path}\n\n"
            summary += f"Test coverage:\n"
            summary += f"  - {len(functions)} function(s): {', '.join([f['name'] for f in functions])}\n" if functions else ""
            summary += f"  - {len(classes)} class(es): {', '.join([c['name'] for c in classes])}\n" if classes else ""
            summary += f"\nTotal tests generated: {len(functions) + sum(1 + len(c['methods'][:3]) for c in classes)}\n"
            summary += f"\n⚠️  Note: Generated tests are templates with TODO markers."
            summary += f"\n    You need to fill in actual test logic and assertions."
            return summary
        else:
            return f"❌ Failed to write test file: {msg}"

    async def fetch_website(
        self,
        ctx: RunContext[None],
        url: str
    ) -> str:
        """
        Fetch and extract content from a specific website URL.

        This tool fetches the full DOM content from a website, converts it to
        LLM-friendly markdown format, and applies smart truncation to stay under
        token limits. Content is cached for 30 minutes by default (configurable).

        Args:
            url: Full URL to fetch (e.g., https://github.com/user/repo)

        Returns:
            Markdown-formatted website content or error message

        Examples:
            - "Read https://github.com/britbrat0/cs676"
            - "What's on https://python.org/downloads"
            - "Fetch https://docs.anthropic.com/api"

        Note:
            - Use this for SPECIFIC URLs
            - Use WebSearchTool for FINDING/SEARCHING content
            - Content is truncated smartly to preserve structure
            - Cached for improved performance
        """
        # Check if crawl4ai is available
        if not HAS_CRAWL4AI:
            return ("❌ Website fetching is not available. The crawl4ai package is not installed.\n\n"
                   "To enable this feature, install it with:\n"
                   "```bash\n"
                   "pip install crawl4ai\n"
                   "playwright install chromium\n"
                   "```")

        # Validate URL
        if not is_valid_url(url):
            return f"❌ Invalid URL format: {url}\n\nPlease provide a valid URL starting with http:// or https://"

        # Track tool call
        self.performance_metrics.track_tool_call("fetch_website", True)

        # Check cache first (Phase 12.2)
        if self.website_cache:
            cached_content = await self.website_cache.get(url)
            if cached_content:
                return f"📄 **Fetched from cache:** {url}\n\n{cached_content}\n\n---\n*Note: Content cached, may not reflect latest changes*"

        # Get config values
        max_tokens = 50000  # default
        truncate_strategy = "smart"  # default

        if self.config:
            max_tokens = self.config.browser_use_max_tokens
            truncate_strategy = self.config.browser_use_truncate_strategy

        # Fetch website content
        success, content = await fetch_website_content(
            url=url,
            max_tokens=max_tokens,
            truncate_strategy=truncate_strategy
        )

        if not success:
            # Track failure
            self.performance_metrics.track_tool_call("fetch_website", False)
            return content  # Error message

        # Cache the content (Phase 12.2)
        if self.website_cache:
            await self.website_cache.set(url, content)

        # Format response
        response = f"📄 **Fetched:** {url}\n\n{content}"

        return response

    async def clear_website_cache(
        self,
        ctx: RunContext[None],
        url: Optional[str] = None
    ) -> str:
        """
        Clear cached website content.

        Args:
            url: Specific URL to clear from cache, or None to clear all cached content

        Returns:
            Success message indicating what was cleared

        Examples:
            - "Clear the cache"
            - "Clear cache for https://github.com/user/repo"
            - "Delete all cached websites"

        Note:
            - Clearing cache will require re-fetching content on next access
            - Useful when you need fresh content or to free up space
        """
        if not self.website_cache:
            return "ℹ️  Website caching is not enabled. No cache to clear."

        try:
            if url:
                # Clear specific URL
                if not is_valid_url(url):
                    return f"❌ Invalid URL format: {url}"

                await self.website_cache.clear(url)
                return f"✓ Cleared cache for: {url}"
            else:
                # Clear all cache
                await self.website_cache.clear()
                return "✓ All website cache cleared successfully"

        except Exception as e:
            return f"❌ Error clearing cache: {str(e)}"

    async def show_cache_stats(
        self,
        ctx: RunContext[None]
    ) -> str:
        """
        Show website cache statistics and information.

        Returns:
            Formatted cache statistics including size, entries, and location

        Examples:
            - "Show cache stats"
            - "How much cache is being used?"
            - "What's cached?"

        Note:
            - Shows total cache size, number of entries, expired entries
            - Helps monitor cache usage and decide when to clear
        """
        if not self.website_cache:
            return ("ℹ️  Website caching is not enabled.\n\n"
                   "To enable caching, add to your ~/.wyn360/config.yaml:\n"
                   "```yaml\n"
                   "browser_use:\n"
                   "  cache:\n"
                   "    enabled: true\n"
                   "```")

        try:
            stats = self.website_cache.get_stats()

            response = "📊 **Website Cache Statistics**\n\n"
            response += f"**Location:** `{stats['cache_dir']}`\n\n"
            response += f"**Total Entries:** {stats['total_entries']}\n"
            response += f"**Total Size:** {stats['total_size_mb']} MB\n"
            response += f"**Expired Entries:** {stats['expired_entries']}\n\n"

            if stats['expired_entries'] > 0:
                response += "💡 *Tip: Expired entries will be automatically cleaned up on next cache access*\n\n"

            if stats['total_entries'] > 0:
                # List cached URLs
                response += "**Cached URLs:**\n"
                for key, entry in self.website_cache.index.items():
                    age_seconds = time.time() - entry['timestamp']
                    age_minutes = int(age_seconds / 60)
                    expired = age_seconds > self.website_cache.ttl

                    status = "❌ Expired" if expired else f"✓ {age_minutes}m old"
                    response += f"- {status}: {entry['url']}\n"

            return response

        except Exception as e:
            return f"❌ Error getting cache stats: {str(e)}"

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
        Process a user message and return complete response.
        CLI will simulate streaming by printing word-by-word.

        This uses pydantic-ai's run() which executes tools properly.

        Args:
            user_message: The user's input message

        Returns:
            Complete response text from the agent
        """
        import time

        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Track response time
            start_time = time.time()

            # Use run() to get complete response (not run_stream)
            # This ensures tools execute properly
            result = await self.agent.run(user_message)

            # Record response time
            duration = time.time() - start_time
            self.performance_metrics.track_request_time(duration)

            # Extract response text
            response_text = getattr(result, 'data', None) or getattr(result, 'output', str(result))
            if not isinstance(response_text, str):
                response_text = str(response_text)

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
                        response_text = response_text + save_message

            # Return complete response
            return response_text

        except Exception as e:
            # Track error
            error_type = type(e).__name__
            self.performance_metrics.track_error(error_type, str(e))

            error_msg = f"\n\nAn error occurred: {str(e)}"
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
        """Clear conversation history and reset token counters and performance metrics."""
        self.conversation_history = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        self.token_history = []
        self.performance_metrics = PerformanceMetrics()  # Reset performance metrics

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
                "performance_metrics": self.performance_metrics.to_dict(),
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

            # Load performance metrics if available
            if "performance_metrics" in session_data:
                self.performance_metrics.from_dict(session_data["performance_metrics"])

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

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance metrics statistics.

        Returns:
            Dictionary with performance metrics
        """
        return self.performance_metrics.get_statistics()

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
