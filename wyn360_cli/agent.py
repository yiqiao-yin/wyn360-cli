"""WYN360 Agent - AI coding assistant using pydantic_ai"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
from pydantic_ai import Agent, RunContext, ModelMessagesTypeAdapter
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
from .credential_manager import CredentialManager
from .session_manager import SessionManager
from .browser_auth import BrowserAuth
from .browser_task_executor import BrowserTaskExecutor
from .document_readers import (
    ExcelReader,
    WordReader,
    PDFReader,
    ImageProcessor,
    ChunkSummarizer,
    ChunkCache,
    ChunkRetriever,
    ChunkMetadata,
    DocumentMetadata,
    EmbeddingModel,
    count_tokens,
    HAS_OPENPYXL,
    HAS_PYTHON_DOCX,
    HAS_PYMUPDF,
    HAS_PDFPLUMBER
)


def _should_use_bedrock() -> bool:
    """
    Check if AWS Bedrock mode is enabled via environment variable.

    Returns:
        True if CLAUDE_CODE_USE_BEDROCK=1, False otherwise
    """
    return os.getenv('CLAUDE_CODE_USE_BEDROCK', '0') == '1'


def _validate_aws_credentials() -> Tuple[bool, str]:
    """
    Validate that required AWS credentials are set.

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if all required credentials present
        - error_message: Error message if invalid, empty string if valid
    """
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        error_msg = f"""AWS Bedrock mode enabled but credentials not found.

Please set the following environment variables:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_SESSION_TOKEN (optional, for temporary credentials)
  - AWS_REGION (optional, defaults to us-east-1)

Missing variables: {', '.join(missing)}

Or disable Bedrock mode:
  unset CLAUDE_CODE_USE_BEDROCK
"""
        return False, error_msg

    return True, ""


class WYN360Agent:
    """
    WYN360 AI coding assistant agent.

    Provides intelligent code generation, file operations, and project assistance
    using Anthropic Claude via pydantic_ai.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        use_history: bool = True,
        config: Optional[WYN360Config] = None,
        use_bedrock: Optional[bool] = None,
        max_search_limit: int = 5
    ):
        """
        Initialize the WYN360 Agent with Anthropic or AWS Bedrock.

        Args:
            api_key: Anthropic API key (required if not using Bedrock)
            model: Claude model to use (default: claude-sonnet-4-20250514)
            use_history: Whether to send conversation history with each request (default: True)
            config: Optional WYN360Config object with user/project configuration
            use_bedrock: Explicitly set Bedrock mode (overrides env var)
            max_search_limit: Maximum number of web searches per session (default: 5)
        """
        self.config = config

        # Determine authentication mode
        # Priority: 1. Explicit parameter, 2. ANTHROPIC_API_KEY, 3. CLAUDE_CODE_USE_BEDROCK
        if use_bedrock is None:
            # Check if ANTHROPIC_API_KEY is set (takes priority over Bedrock)
            if api_key or os.getenv('ANTHROPIC_API_KEY'):
                # If API key is available, use Anthropic API mode
                use_bedrock = False
            else:
                # No API key, check if Bedrock is enabled
                use_bedrock = _should_use_bedrock()

        self.use_bedrock = use_bedrock

        # Model selection priority:
        # 1. ANTHROPIC_MODEL env var (highest priority for runtime override)
        # 2. Config model (if not the default value)
        # 3. Provided model parameter
        # 4. Default based on authentication mode

        env_model = os.getenv('ANTHROPIC_MODEL')
        config_model = config.model if config else None

        if env_model:
            # Environment variable takes highest priority for runtime override
            self.model_name = env_model
        elif config_model and config_model != "claude-sonnet-4-20250514":
            # Use config model if it's explicitly set (not the default)
            self.model_name = config_model
        elif model != "claude-sonnet-4-20250514":
            # Use provided model parameter if it's not the default
            self.model_name = model
        else:
            # Use appropriate default based on authentication mode
            if self.use_bedrock:
                # Bedrock requires ARN format
                self.model_name = "us.anthropic.claude-sonnet-4-20250514-v1:0"
            else:
                # Anthropic API uses model ID format
                self.model_name = "claude-sonnet-4-20250514"

        self.use_history = use_history
        # Phase 5.9: Store pydantic-ai messages for proper context retention
        self.conversation_history: List = []  # Will store pydantic-ai ModelMessage objects

        # Web search limit (configurable, default: 5)
        self.max_search_limit = max_search_limit

        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        self.token_history: List[Dict[str, Any]] = []

        # Document processing token tracking (Phase 13.1)
        self.doc_processing_input_tokens = 0
        self.doc_processing_output_tokens = 0
        self.doc_processing_count = 0

        # Vision API token tracking (Phase 5.1.3)
        self.vision_input_tokens = 0
        self.vision_output_tokens = 0
        self.vision_image_count = 0

        # Document reader settings (Phase 13.1)
        self.doc_token_limits = {
            "excel": 10000,
            "word": 15000,
            "pdf": 20000
        }
        self.image_handling_mode = "describe"  # skip | describe | vision
        self.pdf_engine = "pymupdf"  # pymupdf | pdfplumber

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

        # Authenticated browsing (Phase 4.2 + 4.4)
        self.credential_manager = CredentialManager()
        self.session_manager = SessionManager()

        # Phase 4.4: Debug mode from environment variable
        debug_mode = os.getenv('WYN360_BROWSER_DEBUG', 'false').lower() == 'true'
        self.browser_auth = BrowserAuth(debug=debug_mode)

        # Initialize Anthropic model based on authentication mode
        if self.use_bedrock:
            # AWS Bedrock mode
            is_valid, error_msg = _validate_aws_credentials()
            if not is_valid:
                raise ValueError(error_msg)

            # Import pydantic-ai's Bedrock model
            try:
                from pydantic_ai.models.bedrock import BedrockConverseModel
            except ImportError:
                raise ImportError(
                    "AWS Bedrock support requires pydantic-ai-slim[bedrock] package.\n"
                    "This should be included with pydantic-ai>=1.13.0"
                )

            # Get AWS region from environment or use default
            aws_region = os.getenv('AWS_REGION', 'us-east-1')

            # Set AWS region for boto3 (used by BedrockConverseModel)
            os.environ['AWS_DEFAULT_REGION'] = aws_region

            # Create Bedrock model using pydantic-ai's built-in support
            # BedrockConverseModel automatically reads AWS credentials from environment:
            # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
            self.model = BedrockConverseModel(self.model_name)

            self.api_key = None  # Not used in Bedrock mode

            print(f"🌩️  AWS Bedrock mode enabled")
            print(f"📡 Region: {aws_region}")
            print(f"🤖 Model: {self.model_name}")

        else:
            # Direct Anthropic API mode (existing behavior)
            # Try to get API key from parameter or environment
            if not api_key:
                api_key = os.getenv('ANTHROPIC_API_KEY')

            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is required when not using AWS Bedrock.\n"
                    "Set environment variable: export ANTHROPIC_API_KEY=sk-ant-xxx\n"
                    "Or enable Bedrock mode: export CLAUDE_CODE_USE_BEDROCK=1"
                )

            self.api_key = api_key

            # Set API key in environment for pydantic-ai to use
            os.environ['ANTHROPIC_API_KEY'] = api_key

            # Initialize Anthropic model (it will use the environment variable)
            self.model = AnthropicModel(self.model_name)

        # Create the agent with tools and web search
        # WebSearchTool is now enabled with pydantic-ai >= 1.13.0
        # Note: Bedrock doesn't support builtin_tools, so only enable for Anthropic API
        builtin_tools = []
        if HAS_WEB_SEARCH and not self.use_bedrock:
            # Enable web search with configurable limit (Anthropic API only)
            builtin_tools.append(WebSearchTool(max_uses=self.max_search_limit))

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
                self.show_cache_stats,
                # Authenticated browsing (Phase 4.2)
                self.login_to_website,
                # Autonomous browsing (Phase 5.3)
                self.browse_and_find,
                # Document readers (Phase 13.2, 13.3, 13.4)
                self.read_excel,
                self.read_word,
                self.read_pdf
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

**JUPYTER NOTEBOOK CONVERSIONS:**

When converting .ipynb files to .py scripts:
- **Extract ONLY code cells** - Skip markdown cells, outputs, and explanations
- **Keep it minimal** - Focus on reusable functions and core logic only
- **Break into multiple files** if notebook is large (>800 lines):
  - Example: "makemore_part4_backprop.ipynb" → "makemore_data.py" + "makemore_model.py" + "makemore_train.py"
  - Split by functionality: data processing, model definition, training loop
- **Remove notebook-specific code:**
  - Display commands (display(), Image(), HTML())
  - Inline plots without saving (plt.show() without context)
  - Cell magic commands (%matplotlib, %%time, etc.)
- **Preserve only:**
  - Import statements
  - Function/class definitions
  - Core computational logic
  - Reusable code blocks

**Document Reading (Phase 13):**

When user wants to READ, SEARCH, ANALYZE, or QUERY document files:

**IMPORTANT - Use Built-in Document Tools:**
- For PDF files (.pdf) → Use read_pdf()
- For Excel files (.xlsx, .xls) → Use read_excel()
- For Word documents (.docx) → Use read_word()

**DO NOT write Python scripts to read these documents** - the built-in tools provide:
- Intelligent chunking and summarization (handles large documents)
- Query-based retrieval (semantic search)
- 1-hour caching (instant re-access)
- Structure-aware processing (tables, headings, page ranges)
- Token-efficient summaries with tags

**When to Use Document Tools:**
- "Read report.pdf" → read_pdf("report.pdf")
- "What's in data.xlsx?" → read_excel("data.xlsx")
- "Search for 'budget' in spreadsheet.xlsx" → read_excel("spreadsheet.xlsx", query="budget")
- "Show conclusions in thesis.docx" → read_word("thesis.docx", query="conclusions")
- "Read pages 10-20 of manual.pdf" → read_pdf("manual.pdf", page_range=(10, 20))
- "Find installation steps in guide.pdf" → read_pdf("guide.pdf", query="installation")

**Only write analysis scripts when:**
- User explicitly asks for a .py script (e.g., "write a script to analyze PDF")
- User wants to process MULTIPLE documents programmatically
- User wants custom visualization or data transformation beyond reading

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

"""

        # Web capabilities section - different for Bedrock vs Anthropic API
        if not self.use_bedrock:
            # Anthropic API mode - has WebSearchTool
            base_prompt += f"""**Web Capabilities (Phase 11.1 + 12.1):**

You now have TWO tools for web access:
1. **WebSearchTool** - For searching the web (limited to {self.max_search_limit} uses)
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
- Limited to {self.max_search_limit} searches per session
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
        else:
            # Bedrock mode - no WebSearchTool, only fetch_website
            base_prompt += """**Web Capabilities (Phase 12.1):**

**IMPORTANT - Search Limitation:**
Web search is not available in AWS Bedrock mode. For queries requiring web search:
- Politely inform the user that web search is unavailable in Bedrock mode
- Suggest they use fetch_website() if they have a specific URL
- Otherwise, use your training knowledge to help

**fetch_website() - Available Tool:**
- User provides a SPECIFIC URL: "Read https://github.com/user/repo"
- User wants content from an exact webpage: "What's on https://example.com"
- User says "fetch", "read", "get", or "load" with a URL
- Examples:
  - ✅ "Read https://github.com/britbrat0/cs676" → fetch_website()
  - ✅ "What's on https://python.org/downloads" → fetch_website()
  - ✅ "Fetch https://docs.anthropic.com" → fetch_website()
  - ✅ "Load the content from https://example.com" → fetch_website()

**fetch_website Details:**
- Fetches full DOM content from the URL
- Converts to LLM-friendly markdown
- Smart truncation to stay under token limits
- Cached for 30 minutes (configurable)
- Returns: Full page content, structure preserved
- Max tokens: 50,000 (configurable via config)

**For requests requiring web search (not available):**
When user asks "find popular ML repos" or "what's the weather":
1. Politely explain web search is unavailable in Bedrock mode
2. If you can answer from training knowledge, provide that
3. If they have a specific URL, offer to fetch it with fetch_website()

Example response:
"I'm running in AWS Bedrock mode which doesn't have web search capability. However, I can help you with [alternative based on training knowledge]. If you have a specific URL you'd like me to read, I can fetch that for you!"

**AVOID WEB TOOLS FOR:**
- Code generation (use your training data)
- File operations (use read_file, write_file)
- Local project queries (use list_files, get_project_info)
- Git operations (use git_status, git_diff, git_log)
- General programming concepts you already know
"""

        base_prompt += """

**Authenticated Browsing (Phase 4.2):**

You can now login to websites that require authentication using the login_to_website tool!

**When to use login_to_website:**
- User needs to access content behind a login page
- Website requires authentication to view data
- User wants to automate login for repeated access
- Examples:
  - ✅ "Login to https://wyn360search.com with my credentials"
  - ✅ "Authenticate to https://example.com as user@email.com"
  - ✅ "Sign in to the website with username and password"

**How it works:**
1. **Automatic Form Detection**: Detects login form fields (username, password, submit button)
2. **Browser Automation**: Uses Playwright to automate the login process
3. **Session Management**: Saves session cookies (30-minute TTL) for reuse
4. **Credential Storage**: Optionally encrypts and saves credentials (AES-256-GCM)
5. **Smart Detection**: Identifies CAPTCHA and 2FA requirements

**Workflow:**
1. User provides login URL, username, and password
2. Tool attempts automated login with form detection
3. If successful:
   - Session cookies are saved (30 min TTL)
   - Credentials are encrypted and saved (if save_credentials=True)
   - Use fetch_website() for subsequent authenticated requests
4. If CAPTCHA detected:
   - User is notified to complete manually
5. If 2FA required:
   - User is notified to complete verification manually

**Security Features:**
- Credentials encrypted with AES-256-GCM
- Session cookies stored locally with TTL
- File permissions: 0600 (user read/write only)
- Credentials only decrypted when needed
- Audit log tracks access (no sensitive data)

**Usage Example:**
```
User: Login to https://wyn360search.com with eagle0504 and password123
You: login_to_website(
    url="https://wyn360search.com/login",
    username="eagle0504",
    password="password123"
)

After successful login:
User: Fetch my profile from https://wyn360search.com/profile
You: fetch_website("https://wyn360search.com/profile")  # Automatically uses saved session!
```

**Seamless Integration (Phase 4.3):**
- fetch_website AUTOMATICALLY uses saved sessions when available
- No need to manually pass cookies or session tokens
- After login_to_website, all fetch_website calls to that domain are authenticated
- Sessions persist for 30 minutes (TTL), then auto-expire for security

**Storage Location:**
- Credentials: `~/.wyn360/credentials/vault.enc` (encrypted)
- Sessions: `~/.wyn360/sessions/*.session.json`
- Audit log: `~/.wyn360/logs/auth_audit.log`

**Limitations:**
- CAPTCHA: Requires manual completion (tool will detect and notify)
- 2FA/MFA: Requires manual verification (tool will detect and notify)
- Complex auth flows: May require manual login

**Important Notes:**
- NEVER store credentials in plain text
- ALWAYS use saved sessions when available
- Session TTL: 30 minutes (configurable)
- Credentials are saved per-domain for reuse

**Phase 5: Autonomous Vision-Based Browsing (Anthropic API Only)**

You have access to `browse_and_find()` which enables autonomous multi-step browser automation:

**How it works:**
- Takes screenshots of the browser
- Analyzes with Claude Vision (you see the page)
- Decides what to click, type, or navigate
- Continues until task complete

**Use it for:**
1. Open-ended exploration: "Browse Amazon electronics and tell me what's trending"
2. Multi-step tasks: "Find cheapest sneaker with 2-day shipping"
3. Integrated workflows: Can chain with WebSearchTool, login_to_website, etc.

**Integration with existing tools:**
- If user is logged in (via login_to_website), browse_and_find uses saved session
- Can combine with WebSearchTool: "search for best shoe stores, browse top result"
- Shares context with your main conversation

**Guidelines:**
- Start URL should be the most relevant page for the task
- Task description should be clear and specific
- For complex tasks, break into smaller browse_and_find calls
- Browser is visible by default (user can watch)

**NOT available in Bedrock mode** (requires vision capabilities)
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
                return f"""Error: Content too large ({content_length} bytes, {content_length // 1024}KB). Maximum size is {max_size} bytes ({max_size // 1024}KB).

Your code is too long! Please reduce to under 1000 lines.

**Solutions:**
1. **Break into multiple files** (e.g., part1.py, part2.py, part3.py)
2. **For Jupyter notebook conversions:**
   - Extract ONLY code cells (skip markdown/outputs)
   - Focus on reusable functions and core logic
   - Create separate files for data loading, model, and training
3. **For large scripts:**
   - Split by functionality (utils.py, main.py, config.py)
   - Remove extensive comments/docstrings
   - Keep only essential code

Content preview:
{preview}"""

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

        **Authenticated Browsing (Phase 4.3):**
        Automatically uses saved session cookies if available for the domain.
        After logging in with login_to_website, subsequent fetch_website calls
        will be authenticated automatically.

        Args:
            url: Full URL to fetch (e.g., https://github.com/user/repo)

        Returns:
            Markdown-formatted website content or error message

        Examples:
            - "Read https://github.com/britbrat0/cs676"
            - "What's on https://python.org/downloads"
            - "Fetch https://docs.anthropic.com/api"
            - "Fetch my profile from https://wyn360search.com/profile" (after login)

        Note:
            - Use this for SPECIFIC URLs
            - Use WebSearchTool for FINDING/SEARCHING content
            - Content is truncated smartly to preserve structure
            - Cached for improved performance
            - Automatically authenticated if session exists for domain
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

        # Check for saved session cookies (Phase 4.3)
        cookies = None
        authenticated = False
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        session = self.session_manager.get_session(domain)
        if session:
            cookies = session['cookies']
            authenticated = True

        # Fetch website content
        success, content = await fetch_website_content(
            url=url,
            max_tokens=max_tokens,
            truncate_strategy=truncate_strategy,
            cookies=cookies
        )

        if not success:
            # Track failure
            self.performance_metrics.track_tool_call("fetch_website", False)
            return content  # Error message

        # Cache the content (Phase 12.2)
        if self.website_cache:
            await self.website_cache.set(url, content)

        # Format response (Phase 4.3: Include authentication indicator)
        auth_indicator = " 🔐 (authenticated)" if authenticated else ""
        response = f"📄 **Fetched{auth_indicator}:** {url}\n\n{content}"

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

    async def login_to_website(
        self,
        ctx: RunContext[None],
        url: str,
        username: str,
        password: str,
        save_credentials: bool = True
    ) -> str:
        """
        Login to a website using browser automation (Phase 4.2).

        This tool automates login to websites that require authentication.
        It detects login forms, handles CAPTCHA and 2FA, and saves session cookies
        for reuse in subsequent requests.

        Args:
            url: Login page URL (e.g., "https://wyn360search.com/login")
            username: Login username/email
            password: Login password
            save_credentials: Whether to save credentials for future use (default: True)

        Returns:
            Login status message with details

        Examples:
            - "Login to https://wyn360search.com with user@example.com"
            - "Authenticate to https://github.com"

        Note:
            - Credentials are encrypted with AES-256-GCM
            - Session cookies are saved for 30 minutes (default)
            - CAPTCHA detection: User will be notified to complete manually
            - 2FA detection: User will be prompted for verification code
            - Use fetch_website() with saved session for authenticated requests
        """
        try:
            # Extract domain for session/credential management
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Check if we have a valid session already
            if self.session_manager.is_session_valid(domain):
                return (f"✅ Already authenticated to {domain}\n\n"
                       f"Session is still valid. Use fetch_website() to access authenticated pages.\n"
                       f"To force re-login, clear the session first with: clear_website_cache")

            # Perform login
            result = await self.browser_auth.login(url, username, password)

            if result['success']:
                # Save session cookies
                cookies = result['cookies']
                self.session_manager.save_session(domain, cookies)

                # Save credentials if requested
                if save_credentials:
                    self.credential_manager.save_credential(domain, username, password)

                response = f"✅ Login successful to {domain}!\n\n"
                response += f"**Session Details:**\n"
                response += f"- Domain: {domain}\n"
                response += f"- Username: {username}\n"
                response += f"- Session saved: Yes (30 minutes TTL)\n"
                if save_credentials:
                    response += f"- Credentials saved: Yes (encrypted)\n\n"
                response += f"**Next Steps:**\n"
                response += f"Use fetch_website() to access authenticated pages with this session.\n"

                return response

            elif result['has_captcha']:
                return (f"❌ Login blocked by CAPTCHA\n\n"
                       f"The website requires CAPTCHA completion:\n"
                       f"- URL: {url}\n\n"
                       f"**Action Required:**\n"
                       f"Please login manually in a browser to complete the CAPTCHA.\n"
                       f"Once logged in, you can use the browser's cookies with fetch_website().")

            elif result['requires_2fa']:
                # For now, return message about 2FA
                # In future, could integrate with CLI prompt
                return (f"🔐 2FA Required\n\n"
                       f"The website requires two-factor authentication:\n"
                       f"- URL: {url}\n\n"
                       f"**Action Required:**\n"
                       f"Two-factor authentication must be completed manually.\n"
                       f"Please login through a browser to complete 2FA verification.")

            else:
                return (f"❌ Login failed\n\n"
                       f"**Details:** {result['message']}\n\n"
                       f"**Possible Reasons:**\n"
                       f"- Incorrect username or password\n"
                       f"- Website structure not recognized\n"
                       f"- Login form not detected\n\n"
                       f"Please verify credentials and try again.")

        except Exception as e:
            return f"❌ Error during login: {str(e)}"

    async def login_with_manual_selectors(
        self,
        ctx: RunContext[None],
        url: str,
        username: str,
        password: str,
        username_selector: str,
        password_selector: str,
        submit_selector: Optional[str] = None
    ) -> str:
        """
        Login using manually specified CSS selectors (Phase 4.4.5).

        Use this when automatic form detection fails. You need to inspect the
        website's HTML to find the CSS selectors for the login form fields.

        Args:
            url: Login page URL
            username: Login username/email
            password: Login password
            username_selector: CSS selector for username field (e.g., '#username', 'input[name="user"]')
            password_selector: CSS selector for password field (e.g., '#password', 'input[name="pass"]')
            submit_selector: CSS selector for submit button (optional, will press Enter if not provided)

        Returns:
            Login status message

        Examples:
            - "Login to https://example.com with user/pass using selectors #user, #pass, #submit"
            - "Authenticate with custom selectors: username=#login_user, password=#login_pass"

        Note:
            - Inspect the page HTML to find correct selectors
            - Use browser DevTools (F12) → Elements tab
            - ID selectors: #id_value
            - Name selectors: input[name="value"]
            - Class selectors: .class_name
        """
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            # Check if already authenticated
            if self.session_manager.is_session_valid(domain):
                return (f"✅ Already authenticated to {domain}\n\n"
                       f"Session is still valid. To force re-login, clear the session first.")

            # Perform login with manual selectors
            result = await self.browser_auth.login_with_selectors(
                url=url,
                username=username,
                password=password,
                username_selector=username_selector,
                password_selector=password_selector,
                submit_selector=submit_selector
            )

            if result['success']:
                # Save session
                cookies = result['cookies']
                self.session_manager.save_session(domain, cookies)
                self.credential_manager.save_credential(domain, username, password)

                response = f"✅ Login successful to {domain}! (manual selectors)\n\n"
                response += f"**Session Details:**\n"
                response += f"- Domain: {domain}\n"
                response += f"- Username: {username}\n"
                response += f"- Selectors used:\n"
                response += f"  - Username: {username_selector}\n"
                response += f"  - Password: {password_selector}\n"
                if submit_selector:
                    response += f"  - Submit: {submit_selector}\n"
                response += f"- Session saved: Yes (30 minutes TTL)\n\n"
                response += f"**Next Steps:**\n"
                response += f"Use fetch_website() to access authenticated pages.\n"

                return response

            elif result['has_captcha']:
                return f"❌ CAPTCHA detected. Please complete manually."

            elif result['requires_2fa']:
                return f"🔐 2FA required. Please complete authentication manually."

            else:
                return (f"❌ Login failed with manual selectors\n\n"
                       f"**Details:** {result['message']}\n\n"
                       f"**Troubleshooting:**\n"
                       f"- Verify selectors are correct (inspect page HTML)\n"
                       f"- Check if form requires additional interaction\n"
                       f"- Try waiting for page to fully load\n"
                       f"- Verify credentials are correct")

        except Exception as e:
            return f"❌ Error during manual selector login: {str(e)}"

    async def browse_and_find(
        self,
        ctx: RunContext[None],
        task: str,
        url: str,
        max_steps: int = 20,
        headless: bool = False
    ) -> str:
        """
        Autonomously browse a website to complete a multi-step task using vision.

        **How it works:**
        1. Opens browser (visible by default so you can watch)
        2. Takes screenshots and analyzes with Claude Vision
        3. Makes intelligent decisions about what to click/type/navigate
        4. Continues until task is complete or max_steps reached
        5. Returns extracted information

        **Examples:**
        - "Find the cheapest sneaker with 2-day shipping on Amazon"
        - "Browse electronics section and tell me what's trending"
        - "Search for 'laptop', sort by best rating, get first result's price"
        - "Go to my Amazon wishlist and find the most expensive item"

        **Args:**
            task: Natural language description of what to accomplish
            url: Starting URL (e.g., "https://amazon.com")
            max_steps: Maximum browser actions to attempt (default: 20)
            headless: Run browser invisibly (default: False - visible)

        **Integration:**
        - Works seamlessly with login_to_website (uses saved sessions)
        - Can be chained with WebSearchTool ("search for X, then browse top result")
        - Shares context with main agent

        **IMPORTANT:**
        - Only works in Anthropic API mode (requires vision capabilities)
        - Disabled in Bedrock mode
        - Browser will be visible by default (user can watch the agent work)
        - Set headless=True to run invisibly

        **Returns:**
            Extracted information or task result as formatted text
        """
        import logging
        logger = logging.getLogger(__name__)

        # Check mode (vision required)
        if self.use_bedrock:
            return (
                "❌ Autonomous browsing requires vision capabilities.\n\n"
                "This feature uses Claude Vision to analyze screenshots and make "
                "intelligent navigation decisions. Vision capabilities are not "
                "available in AWS Bedrock mode.\n\n"
                "Please use Anthropic API mode to access this feature:\n"
                "  export ANTHROPIC_API_KEY=your_key_here\n"
                "  unset CLAUDE_CODE_USE_BEDROCK"
            )

        try:
            # Initialize executor
            executor = BrowserTaskExecutor(self.agent)

            # Execute task
            result = await executor.execute_task(
                task=task,
                url=url,
                max_steps=max_steps,
                headless=headless
            )

            # Format response based on status
            if result['status'] == 'success':
                return f"""✅ **Task Completed Successfully!**

**Task:** {task}
**Steps Taken:** {result['steps_taken']}

**Result:**
{self._format_extracted_data(result['result'])}

**Summary:**
{result['reasoning']}

---
*Powered by Claude Vision + Playwright*
"""

            elif result['status'] == 'partial':
                return f"""⚠️ **Task Partially Completed**

**Task:** {task}
**Steps Taken:** {result['steps_taken']} (reached maximum)

**Progress:**
{self._format_action_history(result['history'])}

**Note:** {result['reasoning']}

You may want to:
1. Increase max_steps (currently {max_steps})
2. Refine the task description
3. Try a different starting URL
"""

            else:  # failed
                return f"""❌ **Task Failed**

**Task:** {task}
**Steps Attempted:** {result['steps_taken']}

**Issue:** {result['reasoning']}

**Action History:**
{self._format_action_history(result['history'])}

**Suggestions:**
- Verify the URL is accessible
- Check if the task is achievable on this website
- Try breaking the task into smaller steps
- Consider using manual selectors if form detection failed
"""

        except Exception as e:
            logger.error(f"Autonomous browsing error: {e}")
            return f"❌ Error during autonomous browsing: {str(e)}"

    def _format_extracted_data(self, data: Dict) -> str:
        """Format extracted data for display."""
        if not data:
            return "No data extracted"

        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"**{key}:**")
                lines.append(self._format_data_recursive(value, indent=1))
            else:
                lines.append(f"**{key}:** {value}")

        return '\n'.join(lines)

    def _format_data_recursive(self, data: Any, indent: int = 0) -> str:
        """Recursively format data for display."""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{'  ' * indent}- {key}:")
                    lines.append(self._format_data_recursive(value, indent + 1))
                else:
                    lines.append(f"{'  ' * indent}- {key}: {value}")
            return '\n'.join(lines)
        elif isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(self._format_data_recursive(item, indent))
                else:
                    lines.append(f"{'  ' * indent}- {item}")
            return '\n'.join(lines)
        else:
            return f"{'  ' * indent}{data}"

    def _format_action_history(self, history: List[Dict]) -> str:
        """Format action history for display."""
        if not history:
            return "No actions taken yet"

        lines = []
        for entry in history[-5:]:  # Show last 5 actions
            step = entry.get('step', '?')
            action = entry.get('action', {})
            action_type = action.get('type', 'unknown')
            confidence = entry.get('confidence', 0)
            reasoning = entry.get('reasoning', 'N/A')

            lines.append(f"**Step {step}:** {action_type.upper()}")
            lines.append(f"  - Confidence: {confidence}%")
            lines.append(f"  - Reasoning: {reasoning[:100]}...")

            if action_type == 'click':
                selector = action.get('selector', action.get('text', 'unknown'))
                lines.append(f"  - Target: {selector}")
            elif action_type == 'type':
                selector = action.get('selector', 'unknown')
                lines.append(f"  - Field: {selector}")
            elif action_type == 'navigate':
                nav_url = action.get('url', 'unknown')
                lines.append(f"  - URL: {nav_url}")

            lines.append("")  # Blank line between steps

        return '\n'.join(lines)

    async def read_excel(
        self,
        ctx: RunContext[None],
        file_path: str,
        max_tokens: Optional[int] = None,
        include_sheets: Optional[List[str]] = None,
        use_chunking: bool = True,
        regenerate_cache: bool = False,
        query: Optional[str] = None
    ) -> str:
        """
        **Use this tool when the user wants to read, search, analyze, or query Excel files (.xlsx/.xls).**

        Examples of when to use:
        - "Read data.xlsx"
        - "What's in the spreadsheet?"
        - "Search for 'revenue' in financial_report.xlsx"
        - "Show me the sales data from Q1_data.xlsx"
        - "Analyze the budget spreadsheet"

        Read and intelligently process Excel files (.xlsx/.xls).

        This tool reads Excel files with intelligent chunking, summarization, and
        retrieval. It handles unstructured data (tables not at A1), merged cells,
        evaluated formula values, and converts to markdown format. Results are
        cached for 1 hour by default.

        Args:
            file_path: Path to Excel file (absolute or relative)
            max_tokens: Maximum tokens to process (default: from config, 10000)
            include_sheets: Optional list of sheet names to include
            use_chunking: Whether to use intelligent chunking (default: True)
            regenerate_cache: Force regenerate cache (ignore existing)
            query: Optional query to filter relevant chunks

        Returns:
            Formatted Excel content with summaries and tags

        Examples:
            - "Read expenses.xlsx"
            - "Read data.xlsx and show only Q1 sheet"
            - "What were April expenses in budget.xlsx?"
            - "Summarize sales.xlsx"

        Features:
            - Detects data regions (doesn't assume A1 start)
            - Handles merged cells
            - Shows evaluated formula values
            - Converts to markdown tables
            - Intelligent chunking by sheets/row ranges
            - Claude Haiku summarization (~100 tokens per chunk)
            - Tag generation for efficient retrieval
            - 1-hour TTL cache

        Note:
            Requires openpyxl: pip install openpyxl
        """
        # Check if openpyxl is available
        if not HAS_OPENPYXL:
            return ("❌ **openpyxl not installed**\n\n"
                   "The Excel reader requires openpyxl to be installed.\n\n"
                   "**Install it with:**\n"
                   "```bash\n"
                   "pip install openpyxl\n"
                   "```\n\n"
                   "Then try again.")

        # Track tool call
        self.performance_metrics.track_tool_call("read_excel", True)

        # Resolve file path
        file_path_obj = Path(file_path)
        if not file_path_obj.is_absolute():
            file_path_obj = Path.cwd() / file_path

        if not file_path_obj.exists():
            self.performance_metrics.track_tool_call("read_excel", False)
            return f"❌ File not found: {file_path}"

        # Get max_tokens from config if not specified
        if max_tokens is None:
            max_tokens = self.doc_token_limits.get("excel", 10000)

        # Initialize cache
        cache = ChunkCache()

        # Check cache (unless regenerate requested)
        cached_data = None
        if not regenerate_cache:
            cached_data = cache.load_chunks(str(file_path_obj))

        if cached_data:
            # Use cached data
            metadata = cached_data["metadata"]
            chunks = cached_data["chunks"]

            response = f"📊 **Excel File (from cache):** `{file_path_obj.name}`\n\n"
            response += f"**Sheets:** {metadata['chunk_count']} | "
            response += f"**Total Tokens:** {metadata['total_tokens']:,}\n\n"
        else:
            # Read Excel file
            try:
                # Determine chunk size
                chunk_size = min(max_tokens // 2, 1000)  # Use half of max for chunking

                reader = ExcelReader(
                    file_path=str(file_path_obj),
                    chunk_size=chunk_size,
                    include_sheets=include_sheets
                )

                # Read sheets
                excel_data = reader.read()

                if excel_data["total_sheets"] == 0:
                    return f"❌ No sheets found in {file_path_obj.name}"

                # Chunk sheets
                chunks_data = reader.chunk_sheets(excel_data["sheets"])

                # Summarize chunks using Claude Haiku (if chunking enabled)
                chunks_metadata = []
                summarizer = ChunkSummarizer(
                    api_key=self.api_key,
                    enable_embeddings=True  # Phase 5.2: Enable semantic matching
                ) if use_chunking else None

                # Initialize embedding model for semantic matching (Phase 5.2)
                embedding_model = None
                if use_chunking:
                    try:
                        embedding_model = EmbeddingModel()
                    except Exception as e:
                        # If embeddings fail, continue without them
                        pass

                # Phase 5.6.1: Parallel Chunk Summarization
                # Separate chunks into those needing summarization and small chunks
                chunks_to_summarize = []
                chunks_to_summarize_indices = []

                for i, chunk_data in enumerate(chunks_data):
                    if use_chunking and chunk_data["tokens"] > 200:
                        chunks_to_summarize.append({
                            "content": chunk_data["content"],
                            "context": {
                                "doc_type": "excel",
                                "sheet_name": chunk_data["sheet_name"]
                            }
                        })
                        chunks_to_summarize_indices.append(i)

                # Summarize chunks in parallel (batch_size=10)
                if chunks_to_summarize:
                    summary_results = await summarizer.summarize_chunks_parallel(
                        chunks_to_summarize,
                        batch_size=10
                    )

                    # Track tokens for all summarized chunks
                    for summary_result in summary_results:
                        if "api_tokens" in summary_result:
                            self.track_document_processing(
                                summary_result["api_tokens"]["input"],
                                summary_result["api_tokens"]["output"]
                            )

                # Build chunk metadata (preserve original order)
                summary_idx = 0
                for i, chunk_data in enumerate(chunks_data):
                    chunk_content = chunk_data["content"]
                    chunk_tokens = chunk_data["tokens"]

                    if i in chunks_to_summarize_indices:
                        # Use parallel summarization result
                        summary_result = summary_results[summary_idx]
                        summary_idx += 1

                        chunk_metadata = ChunkMetadata(
                            chunk_id=chunk_data["chunk_id"],
                            position=chunk_data["position"],
                            summary=summary_result["summary"],
                            tags=summary_result["tags"],
                            token_count=chunk_tokens,
                            summary_tokens=summary_result.get("summary_tokens", 0),
                            tag_tokens=summary_result.get("tag_tokens", 0),
                            sheet_name=chunk_data["sheet_name"]
                        )
                    else:
                        # Small chunk - use as-is
                        chunk_metadata = ChunkMetadata(
                            chunk_id=chunk_data["chunk_id"],
                            position=chunk_data["position"],
                            summary=chunk_content[:400] + "..." if len(chunk_content) > 400 else chunk_content,
                            tags=[chunk_data["sheet_name"]],
                            token_count=chunk_tokens,
                            summary_tokens=chunk_tokens,
                            tag_tokens=0,
                            sheet_name=chunk_data["sheet_name"]
                        )

                    chunks_metadata.append(chunk_metadata)

                # Add semantic embeddings to chunks (Phase 5.2.2)
                if summarizer and summarizer.enable_embeddings:
                    # Convert ChunkMetadata objects to dicts for embedding
                    chunks_dicts = [asdict(chunk) if hasattr(chunk, '__dict__') else chunk.__dict__ for chunk in chunks_metadata]
                    chunks_dicts = summarizer.add_embeddings_to_chunks(chunks_dicts)

                    # Update chunks_metadata with embeddings
                    for i, chunk_dict in enumerate(chunks_dicts):
                        if "embedding" in chunk_dict:
                            chunks_metadata[i].embedding = chunk_dict["embedding"]

                # Save to cache
                doc_metadata = DocumentMetadata(
                    file_path=str(file_path_obj),
                    file_hash=cache.get_file_hash(str(file_path_obj)),
                    file_size=file_path_obj.stat().st_size,
                    total_tokens=excel_data["total_tokens"],
                    chunk_count=len(chunks_metadata),
                    chunk_size=chunk_size,
                    created_at=time.time(),
                    ttl=cache.ttl,
                    doc_type="excel"
                )

                cache.save_chunks(str(file_path_obj), doc_metadata, chunks_metadata)

                metadata = doc_metadata
                chunks = [chunk.__dict__ if hasattr(chunk, '__dict__') else chunk for chunk in chunks_metadata]

                response = f"📊 **Excel File:** `{file_path_obj.name}`\n\n"
                response += f"**Sheets:** {excel_data['total_sheets']} | "
                response += f"**Total Tokens:** {excel_data['total_tokens']:,} | "
                response += f"**Chunks:** {len(chunks)}\n\n"

            except Exception as e:
                self.performance_metrics.track_tool_call("read_excel", False)
                return f"❌ Error reading Excel file: {str(e)}"

        # Filter chunks by query if provided (Phase 5.2.3: Semantic matching)
        if query:
            retriever = ChunkRetriever(
                top_k=3,
                embedding_model=embedding_model  # Use semantic matching if available
            )
            chunks = retriever.get_relevant_chunks(query, chunks)
            response += f"🔍 **Query:** \"{query}\"\n"
            response += f"**Relevant Chunks:** {len(chunks)}\n\n"

        # Format output
        response += "---\n\n"

        for chunk in chunks:
            sheet_name = chunk.get("sheet_name", "Unknown")
            summary = chunk.get("summary", "")
            tags = chunk.get("tags", [])

            response += f"### {sheet_name}\n\n"
            response += f"{summary}\n\n"
            response += f"**Tags:** {', '.join(tags)}\n\n"
            response += "---\n\n"

        # Add cache note
        response += f"\n*Note: Content cached for 1 hour. Use regenerate_cache=True to refresh.*"

        return response

    async def read_word(
        self,
        ctx: RunContext[None],
        file_path: str,
        max_tokens: Optional[int] = None,
        use_chunking: bool = True,
        image_handling: Optional[str] = None,
        regenerate_cache: bool = False,
        query: Optional[str] = None
    ) -> str:
        """
        **Use this tool when the user wants to read, search, analyze, or query Word documents (.docx).**

        Examples of when to use:
        - "Read report.docx"
        - "What's in the thesis document?"
        - "Find the methodology section in research.docx"
        - "Show me the conclusions from project_report.docx"
        - "Search for 'requirements' in specification.docx"

        Read and intelligently process Word documents (.docx).

        This tool reads Word documents with structure-aware chunking, summarization,
        and retrieval. It extracts headings, paragraphs, tables, and lists, converting
        to markdown format. Handles document hierarchy and preserves structure. Results
        are cached for 1 hour by default.

        Args:
            file_path: Path to Word file (absolute or relative)
            max_tokens: Maximum tokens to process (default: from config, 15000)
            use_chunking: Whether to use intelligent chunking (default: True)
            image_handling: How to handle images (skip|describe|vision, default: from config)
            regenerate_cache: Force regenerate cache (ignore existing)
            query: Optional query to filter relevant sections

        Returns:
            Formatted Word content with summaries and tags

        Examples:
            - "Read paper.docx"
            - "Read report.docx and show only the methodology section"
            - "What are the conclusions in thesis.docx?"
            - "Summarize document.docx"

        Features:
            - Extracts document structure (headings, paragraphs, tables, lists)
            - Preserves hierarchy (H1, H2, H3 → #, ##, ###)
            - Converts tables to markdown
            - Structure-aware chunking by sections
            - Claude Haiku summarization (~100 tokens per chunk)
            - Tag generation for efficient retrieval
            - 1-hour TTL cache
            - Image handling: skip/describe/vision

        Note:
            Requires python-docx: pip install python-docx
        """
        # Check if python-docx is available
        if not HAS_PYTHON_DOCX:
            return ("❌ **python-docx not installed**\n\n"
                   "The Word reader requires python-docx to be installed.\n\n"
                   "**Install it with:**\n"
                   "```bash\n"
                   "pip install python-docx\n"
                   "```\n\n"
                   "Then try again.")

        # Track tool call
        self.performance_metrics.track_tool_call("read_word", True)

        # Resolve file path
        file_path_obj = Path(file_path)
        if not file_path_obj.is_absolute():
            file_path_obj = Path.cwd() / file_path

        if not file_path_obj.exists():
            self.performance_metrics.track_tool_call("read_word", False)
            return f"❌ File not found: {file_path}"

        # Get max_tokens from config if not specified
        if max_tokens is None:
            max_tokens = self.doc_token_limits.get("word", 15000)

        # Get image_handling from config if not specified
        if image_handling is None:
            image_handling = self.image_handling_mode

        # Initialize cache
        cache = ChunkCache()

        # Check cache (unless regenerate requested)
        cached_data = None
        if not regenerate_cache:
            cached_data = cache.load_chunks(str(file_path_obj))

        if cached_data:
            # Use cached data
            metadata = cached_data["metadata"]
            chunks = cached_data["chunks"]

            response = f"📄 **Word Document (from cache):** `{file_path_obj.name}`\n\n"
            response += f"**Sections:** {metadata['chunk_count']} | "
            response += f"**Total Tokens:** {metadata['total_tokens']:,}\n\n"
        else:
            # Read Word file
            try:
                # Determine chunk size
                chunk_size = min(max_tokens // 2, 1000)  # Use half of max for chunking

                reader = WordReader(
                    file_path=str(file_path_obj),
                    chunk_size=chunk_size,
                    image_handling=image_handling
                )

                # Create ImageProcessor if vision mode enabled
                image_processor = None
                if image_handling == "vision":
                    image_processor = ImageProcessor(api_key=self.api_key, model=self.model_name)

                # Read sections (async with optional vision processing)
                word_data = await reader.read(image_processor=image_processor)

                # Track vision tokens if images were processed
                if "vision_tokens_used" in word_data and word_data["vision_tokens_used"] > 0:
                    # Estimate input tokens (images are ~1000 tokens each, plus prompt ~100)
                    image_count = len(word_data.get("images", []))
                    estimated_input = image_count * 1100
                    self.track_vision_processing(
                        input_tokens=estimated_input,
                        output_tokens=word_data["vision_tokens_used"],
                        image_count=image_count
                    )

                if word_data["total_sections"] == 0:
                    return f"❌ No content found in {file_path_obj.name}"

                # Chunk sections
                chunks_data = reader.chunk_sections(word_data["sections"])

                # Summarize chunks using Claude Haiku (if chunking enabled)
                chunks_metadata = []
                summarizer = ChunkSummarizer(
                    api_key=self.api_key,
                    enable_embeddings=True  # Phase 5.2: Enable semantic matching
                ) if use_chunking else None

                # Initialize embedding model for semantic matching (Phase 5.2)
                embedding_model = None
                if use_chunking:
                    try:
                        embedding_model = EmbeddingModel()
                    except Exception as e:
                        # If embeddings fail, continue without them
                        pass

                # Phase 5.6.1: Parallel Chunk Summarization
                chunks_to_summarize = []
                chunks_to_summarize_indices = []

                for i, chunk_data in enumerate(chunks_data):
                    if use_chunking and chunk_data["tokens"] > 200:
                        chunks_to_summarize.append({
                            "content": chunk_data["content"],
                            "context": {
                                "doc_type": "word",
                                "section_title": chunk_data["section_title"]
                            }
                        })
                        chunks_to_summarize_indices.append(i)

                # Summarize chunks in parallel
                if chunks_to_summarize:
                    summary_results = await summarizer.summarize_chunks_parallel(
                        chunks_to_summarize,
                        batch_size=10
                    )

                    # Track tokens
                    for summary_result in summary_results:
                        if "api_tokens" in summary_result:
                            self.track_document_processing(
                                summary_result["api_tokens"]["input"],
                                summary_result["api_tokens"]["output"]
                            )

                # Build chunk metadata
                summary_idx = 0
                for i, chunk_data in enumerate(chunks_data):
                    chunk_content = chunk_data["content"]
                    chunk_tokens = chunk_data["tokens"]

                    if i in chunks_to_summarize_indices:
                        summary_result = summary_results[summary_idx]
                        summary_idx += 1

                        chunk_metadata = ChunkMetadata(
                            chunk_id=chunk_data["chunk_id"],
                            position=chunk_data["position"],
                            summary=summary_result["summary"],
                            tags=summary_result["tags"],
                            token_count=chunk_tokens,
                            summary_tokens=summary_result.get("summary_tokens", 0),
                            tag_tokens=summary_result.get("tag_tokens", 0),
                            section_title=chunk_data["section_title"]
                        )
                    else:
                        # Small chunk - use as-is
                        chunk_metadata = ChunkMetadata(
                            chunk_id=chunk_data["chunk_id"],
                            position=chunk_data["position"],
                            summary=chunk_content[:400] + "..." if len(chunk_content) > 400 else chunk_content,
                            tags=[chunk_data["section_title"]],
                            token_count=chunk_tokens,
                            summary_tokens=chunk_tokens,
                            tag_tokens=0,
                            section_title=chunk_data["section_title"]
                        )

                    chunks_metadata.append(chunk_metadata)

                # Add semantic embeddings to chunks (Phase 5.2.2)
                if summarizer and summarizer.enable_embeddings:
                    # Convert ChunkMetadata objects to dicts for embedding
                    chunks_dicts = [asdict(chunk) if hasattr(chunk, '__dict__') else chunk.__dict__ for chunk in chunks_metadata]
                    chunks_dicts = summarizer.add_embeddings_to_chunks(chunks_dicts)

                    # Update chunks_metadata with embeddings
                    for i, chunk_dict in enumerate(chunks_dicts):
                        if "embedding" in chunk_dict:
                            chunks_metadata[i].embedding = chunk_dict["embedding"]

                # Save to cache
                doc_metadata = DocumentMetadata(
                    file_path=str(file_path_obj),
                    file_hash=cache.get_file_hash(str(file_path_obj)),
                    file_size=file_path_obj.stat().st_size,
                    total_tokens=word_data["total_tokens"],
                    chunk_count=len(chunks_metadata),
                    chunk_size=chunk_size,
                    created_at=time.time(),
                    ttl=cache.ttl,
                    doc_type="word"
                )

                cache.save_chunks(str(file_path_obj), doc_metadata, chunks_metadata)

                metadata = doc_metadata
                chunks = [chunk.__dict__ if hasattr(chunk, '__dict__') else chunk for chunk in chunks_metadata]

                response = f"📄 **Word Document:** `{file_path_obj.name}`\n\n"
                response += f"**Sections:** {word_data['total_sections']} | "
                response += f"**Total Tokens:** {word_data['total_tokens']:,} | "
                response += f"**Chunks:** {len(chunks)}\n\n"

            except Exception as e:
                self.performance_metrics.track_tool_call("read_word", False)
                return f"❌ Error reading Word file: {str(e)}"

        # Filter chunks by query if provided (Phase 5.2.3: Semantic matching)
        if query:
            retriever = ChunkRetriever(
                top_k=3,
                embedding_model=embedding_model  # Use semantic matching if available
            )
            chunks = retriever.get_relevant_chunks(query, chunks)
            response += f"🔍 **Query:** \"{query}\"\n"
            response += f"**Relevant Chunks:** {len(chunks)}\n\n"

        # Format output
        response += "---\n\n"

        for chunk in chunks:
            section_title = chunk.get("section_title", "Unknown")
            summary = chunk.get("summary", "")
            tags = chunk.get("tags", [])

            response += f"### {section_title}\n\n"
            response += f"{summary}\n\n"
            response += f"**Tags:** {', '.join(tags)}\n\n"
            response += "---\n\n"

        # Add cache note
        response += f"\n*Note: Content cached for 1 hour. Use regenerate_cache=True to refresh.*"

        return response

    async def read_pdf(
        self,
        ctx: RunContext[None],
        file_path: str,
        max_tokens: Optional[int] = None,
        page_range: Optional[Tuple[int, int]] = None,
        use_chunking: bool = True,
        pdf_engine: Optional[str] = None,
        image_handling: Optional[str] = None,
        regenerate_cache: bool = False,
        query: Optional[str] = None
    ) -> str:
        """
        **Use this tool when the user wants to read, search, analyze, or query PDF files.**

        Examples of when to use:
        - "Read research_paper.pdf"
        - "What's in the annual report?"
        - "Search for 'machine learning' in textbook.pdf"
        - "Show me pages 10-20 of the manual"
        - "Find installation instructions in user_guide.pdf"
        - "Summarize the executive summary in proposal.pdf"

        Read and intelligently process PDF files with chunking, summarization, and retrieval.

        Features:
        - Page-by-page extraction with table detection
        - Support for both pymupdf (fast) and pdfplumber (better tables)
        - Page-aware chunking (3-5 pages per chunk)
        - Auto-summarization of each chunk
        - Tag generation for query-based retrieval
        - 1-hour caching for instant re-access
        - Page range filtering for large documents

        Args:
            file_path: Path to PDF file
            max_tokens: Maximum tokens to process (default from config: 20000)
            page_range: Optional (start_page, end_page) to read only specific pages (1-indexed)
            use_chunking: Whether to chunk and summarize (default True)
            pdf_engine: PDF engine to use ("pymupdf" or "pdfplumber", default from config)
            regenerate_cache: Force regenerate cache even if exists
            query: Optional query to retrieve relevant pages

        Returns:
            Formatted document content with summaries and tags

        Example:
            # Read entire PDF
            content = await agent.read_pdf("report.pdf")

            # Read specific pages
            content = await agent.read_pdf("textbook.pdf", page_range=(50, 75))

            # Query for specific content
            content = await agent.read_pdf("manual.pdf", query="installation steps")

            # Use pdfplumber for better table extraction
            content = await agent.read_pdf("data.pdf", pdf_engine="pdfplumber")
        """
        # Check dependencies
        if not HAS_PYMUPDF and not HAS_PDFPLUMBER:
            return (
                "❌ No PDF library installed.\n\n"
                "Install either:\n"
                "- pymupdf (recommended, fast): pip install pymupdf\n"
                "- pdfplumber (better for tables): pip install pdfplumber"
            )

        # Get PDF engine from config if not specified
        if pdf_engine is None:
            pdf_engine = self.pdf_engine

        # Get image_handling from config if not specified
        if image_handling is None:
            image_handling = self.image_handling_mode

        # Validate engine and check if it's available
        if pdf_engine == "pymupdf" and not HAS_PYMUPDF:
            return (
                f"❌ pymupdf not installed.\n\n"
                f"Install with: pip install pymupdf\n"
                f"Or switch to pdfplumber: /set_pdf_engine pdfplumber"
            )
        elif pdf_engine == "pdfplumber" and not HAS_PDFPLUMBER:
            return (
                f"❌ pdfplumber not installed.\n\n"
                f"Install with: pip install pdfplumber\n"
                f"Or switch to pymupdf: /set_pdf_engine pymupdf"
            )

        # Resolve file path (handle relative and absolute paths)
        file_path_obj = Path(file_path)
        if not file_path_obj.is_absolute():
            file_path_obj = Path.cwd() / file_path

        if not file_path_obj.exists():
            return f"❌ File not found: {file_path_obj}"

        # Get max_tokens from config
        if max_tokens is None:
            max_tokens = self.doc_token_limits.get("pdf", 20000)

        # Initialize cache
        cache = ChunkCache(cache_dir=self.cache_dir / "documents")

        # Check cache (unless regenerate requested)
        cache_key = str(file_path_obj)
        if not regenerate_cache:
            cached = cache.load_chunks(cache_key)
            if cached:
                # Cache hit
                chunks = cached

                # Filter by query if provided
                if query:
                    retriever = ChunkRetriever(top_k=5)
                    chunks = retriever.get_relevant_chunks(chunks, query)

                # Format output
                response = "📄 **PDF File (from cache)**\n\n"
                response += f"**File:** {file_path_obj.name}\n"
                response += f"**Pages:** {chunks[0]['metadata'].get('total_pages', 'N/A')}\n"
                response += f"**Chunks:** {len(chunks)}\n"
                if query:
                    response += f"**Query:** {query} (showing top {len(chunks)} relevant chunks)\n"
                response += "\n---\n\n"

                # Show chunk summaries
                for chunk in chunks[:10]:  # Limit to 10 chunks
                    page_range_str = f"Pages {chunk['metadata'].get('start_page', '?')}-{chunk['metadata'].get('end_page', '?')}"
                    summary = chunk["metadata"].get("summary", "No summary available")
                    tags = chunk["metadata"].get("tags", [])

                    response += f"### {page_range_str}\n\n"
                    response += f"{summary}\n\n"
                    response += f"**Tags:** {', '.join(tags)}\n\n"
                    response += "---\n\n"

                response += f"\n*Note: Cached content. Use regenerate_cache=True to refresh.*"
                return response

        # Cache miss or regenerate - read and process PDF
        try:
            reader = PDFReader(
                file_path=str(file_path_obj),
                chunk_size=1000,
                engine=pdf_engine,
                image_handling=image_handling
            )

            # Create ImageProcessor if vision mode enabled
            image_processor = None
            if image_handling == "vision":
                image_processor = ImageProcessor(api_key=self.api_key, model=self.model_name)

            # Read PDF (async with optional vision processing)
            result = await reader.read(page_range=page_range, image_processor=image_processor)

            # Track vision tokens if images were processed
            if "vision_tokens_used" in result and result["vision_tokens_used"] > 0:
                # Estimate input tokens (images are ~1000 tokens each, plus prompt ~100)
                image_count = len(result.get("images", []))
                estimated_input = image_count * 1100
                self.track_vision_processing(
                    input_tokens=estimated_input,
                    output_tokens=result["vision_tokens_used"],
                    image_count=image_count
                )

            total_pages = result["total_pages"]
            pages = result["pages"]
            total_tokens = result["total_tokens"]
            page_range_read = result["page_range_read"]
            has_tables = result["has_tables"]

            # Check if we exceed token limit
            if total_tokens > max_tokens:
                # Truncate or warn
                response = f"⚠️ PDF has {total_tokens} tokens (limit: {max_tokens})\n\n"
                if not use_chunking:
                    return response + "Enable chunking with use_chunking=True for intelligent summarization."

            if not use_chunking:
                # Return raw pages (up to token limit)
                response = f"📄 **PDF File**\n\n"
                response += f"**File:** {file_path_obj.name}\n"
                response += f"**Total Pages:** {total_pages}\n"
                response += f"**Pages Read:** {page_range_read[0]}-{page_range_read[1]}\n"
                response += f"**Tokens:** {total_tokens}\n"
                response += f"**Has Tables:** {'Yes' if has_tables else 'No'}\n"
                response += "\n---\n\n"

                # Include page content (up to limit)
                current_tokens = 0
                for page in pages:
                    if current_tokens + page["tokens"] > max_tokens:
                        break
                    response += f"## Page {page['page_number']}\n\n"
                    response += page["content"] + "\n\n"
                    response += "---\n\n"
                    current_tokens += page["tokens"]

                if current_tokens < total_tokens:
                    response += f"\n*Note: Content truncated at {max_tokens} tokens. Use chunking for full access.*"

                return response

            # Chunk pages
            chunks_data = reader.chunk_pages(pages)

            if not chunks_data:
                return "❌ No content extracted from PDF."

            # Initialize summarizer (Phase 5.2: Enable semantic matching)
            summarizer = ChunkSummarizer(
                api_key=self.api_key,
                model="claude-3-5-haiku-20241022",
                enable_embeddings=True
            )

            # Initialize embedding model for semantic matching (Phase 5.2)
            embedding_model = None
            try:
                embedding_model = EmbeddingModel()
            except Exception as e:
                # If embeddings fail, continue without them
                pass

            # Phase 5.6.1: Parallel Chunk Summarization
            chunks_to_summarize = []
            for chunk_data in chunks_data:
                chunks_to_summarize.append({
                    "content": chunk_data["content"],
                    "context": {
                        "file_name": file_path_obj.name,
                        "doc_type": "pdf",
                        "page_range": f"Pages {chunk_data['page_range'][0]}-{chunk_data['page_range'][1]}",
                        "total_pages": total_pages,
                        "has_tables": chunk_data.get("has_tables", False)
                    }
                })

            # Summarize chunks in parallel
            summary_results = await summarizer.summarize_chunks_parallel(
                chunks_to_summarize,
                batch_size=10
            )

            # Build chunks with metadata
            chunks_with_metadata = []
            total_summary_tokens = 0

            for i, chunk_data in enumerate(chunks_data):
                summary_result = summary_results[i]

                # Track tokens
                if "api_tokens" in summary_result:
                    total_summary_tokens += summary_result["api_tokens"]["input"]
                    total_summary_tokens += summary_result["api_tokens"]["output"]

                # Store chunk with metadata
                chunks_with_metadata.append({
                    "content": chunk_data["content"],
                    "metadata": {
                        "chunk_id": chunk_data["chunk_id"],
                        "start_page": chunk_data["page_range"][0],
                        "end_page": chunk_data["page_range"][1],
                        "tokens": chunk_data["tokens"],
                        "has_tables": chunk_data.get("has_tables", False),
                        "summary": summary_result["summary"],
                        "tags": summary_result["tags"],
                        "summary_tokens": summary_result.get("summary_tokens", 0),
                        "total_pages": total_pages,
                        "pdf_engine": pdf_engine
                    }
                })

            # Track document processing tokens
            self.track_document_processing(total_summary_tokens)

            # Add semantic embeddings to chunks (Phase 5.2.2)
            if summarizer.enable_embeddings:
                # Extract summary/tags from metadata for embedding
                chunks_for_embedding = []
                for chunk in chunks_with_metadata:
                    chunks_for_embedding.append({
                        "summary": chunk["metadata"]["summary"],
                        "tags": chunk["metadata"]["tags"]
                    })

                # Add embeddings
                chunks_for_embedding = summarizer.add_embeddings_to_chunks(chunks_for_embedding)

                # Update original chunks with embeddings
                for i, chunk in enumerate(chunks_with_metadata):
                    if "embedding" in chunks_for_embedding[i]:
                        chunk["metadata"]["embedding"] = chunks_for_embedding[i]["embedding"]

            # Cache chunks
            cache.save_chunks(cache_key, chunks_with_metadata, file_size=file_path_obj.stat().st_size)

            # Filter by query if provided (Phase 5.2.3: Semantic matching)
            if query:
                retriever = ChunkRetriever(
                    top_k=5,
                    embedding_model=embedding_model  # Use semantic matching if available
                )
                chunks_with_metadata = retriever.get_relevant_chunks(query, chunks_with_metadata)

            # Format output
            response = "📄 **PDF File**\n\n"
            response += f"**File:** {file_path_obj.name}\n"
            response += f"**Total Pages:** {total_pages}\n"
            if page_range:
                response += f"**Pages Read:** {page_range_read[0]}-{page_range_read[1]}\n"
            response += f"**Total Tokens:** {total_tokens:,}\n"
            response += f"**Chunks:** {len(chunks_with_metadata)}\n"
            response += f"**Engine:** {pdf_engine}\n"
            response += f"**Has Tables:** {'Yes' if has_tables else 'No'}\n"
            if query:
                response += f"**Query:** {query} (showing top {len(chunks_with_metadata)} relevant chunks)\n"
            response += f"**Summary Tokens Used:** {total_summary_tokens:,}\n"
            response += "\n---\n\n"

            # Show chunk summaries
            for chunk in chunks_with_metadata[:10]:  # Limit to 10 chunks
                page_range_str = f"Pages {chunk['metadata'].get('start_page', '?')}-{chunk['metadata'].get('end_page', '?')}"
                summary = chunk["metadata"].get("summary", "No summary available")
                tags = chunk["metadata"].get("tags", [])

                response += f"### {page_range_str}\n\n"
                response += f"{summary}\n\n"
                response += f"**Tags:** {', '.join(tags)}\n\n"
                response += "---\n\n"

            # Add cache note
            response += f"\n*Note: Content cached for 1 hour. Use regenerate_cache=True to refresh.*"

            return response

        except FileNotFoundError:
            return f"❌ File not found: {file_path_obj}"
        except ImportError as e:
            return f"❌ Import error: {str(e)}"
        except Exception as e:
            return f"❌ Error reading PDF: {str(e)}"

    async def chat(self, user_message: str) -> str:
        """
        Process a user message and generate a response.

        Args:
            user_message: The user's input message

        Returns:
            Agent's response
        """
        try:
            # Run the agent with message history (Phase 5.9: Fix context retention)
            # Pass conversation history to maintain context across turns
            result = await self.agent.run(
                user_message,
                message_history=self.conversation_history if self.use_history else []
            )

            # Extract the response (handle both .data and .output for compatibility)
            response_text = getattr(result, 'data', None) or getattr(result, 'output', str(result))

            # Update conversation history with all messages from this run
            # This includes user message, tool calls, tool responses, and assistant response
            if self.use_history:
                self.conversation_history = result.all_messages()

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
            # Track response time
            start_time = time.time()

            # Run the agent with message history (Phase 5.9: Fix context retention)
            # Pass conversation history to maintain context across turns
            result = await self.agent.run(
                user_message,
                message_history=self.conversation_history if self.use_history else []
            )

            # Record response time
            duration = time.time() - start_time
            self.performance_metrics.track_request_time(duration)

            # Extract response text
            response_text = getattr(result, 'data', None) or getattr(result, 'output', str(result))
            if not isinstance(response_text, str):
                response_text = str(response_text)

            # Update conversation history with all messages from this run
            # This includes user message, tool calls, tool responses, and assistant response
            if self.use_history:
                self.conversation_history = result.all_messages()

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
        self.doc_processing_input_tokens = 0
        self.doc_processing_output_tokens = 0
        self.doc_processing_count = 0
        self.performance_metrics = PerformanceMetrics()  # Reset performance metrics

    def get_history(self) -> List:
        """
        Get current conversation history.

        Returns:
            List of pydantic-ai ModelMessage objects (Phase 5.9: changed from dict format)
        """
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
        from pydantic_core import to_jsonable_python

        try:
            # Phase 5.9: Serialize pydantic-ai messages properly
            conversation_history_json = to_jsonable_python(self.conversation_history)

            session_data = {
                "model": self.model_name,
                "conversation_history": conversation_history_json,
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "request_count": self.request_count,
                "token_history": self.token_history,
                "doc_processing_input_tokens": self.doc_processing_input_tokens,
                "doc_processing_output_tokens": self.doc_processing_output_tokens,
                "doc_processing_count": self.doc_processing_count,
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

            # Phase 5.9: Deserialize pydantic-ai messages properly
            history_json = session_data.get("conversation_history", [])
            if history_json:
                self.conversation_history = ModelMessagesTypeAdapter.validate_python(history_json)
            else:
                self.conversation_history = []

            self.total_input_tokens = session_data.get("total_input_tokens", 0)
            self.total_output_tokens = session_data.get("total_output_tokens", 0)
            self.request_count = session_data.get("request_count", 0)
            self.token_history = session_data.get("token_history", [])
            self.doc_processing_input_tokens = session_data.get("doc_processing_input_tokens", 0)
            self.doc_processing_output_tokens = session_data.get("doc_processing_output_tokens", 0)
            self.doc_processing_count = session_data.get("doc_processing_count", 0)

            # Load performance metrics if available
            if "performance_metrics" in session_data:
                self.performance_metrics.from_dict(session_data["performance_metrics"])

            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False

    def track_document_processing(self, input_tokens: int, output_tokens: int) -> None:
        """
        Track tokens used for document processing (chunk summarization).

        Args:
            input_tokens: Input tokens (chunk content)
            output_tokens: Output tokens (summary + tags)
        """
        self.doc_processing_input_tokens += input_tokens
        self.doc_processing_output_tokens += output_tokens
        self.doc_processing_count += 1

    def track_vision_processing(self, input_tokens: int, output_tokens: int, image_count: int = 1) -> None:
        """
        Track tokens used for vision API calls (image processing).

        Args:
            input_tokens: Input tokens (image + prompt)
            output_tokens: Output tokens (image description)
            image_count: Number of images processed
        """
        self.vision_input_tokens += input_tokens
        self.vision_output_tokens += output_tokens
        self.vision_image_count += image_count

    def get_token_stats(self) -> Dict[str, Any]:
        """
        Get token usage statistics.

        Returns:
            Dictionary with token usage stats
        """
        # Regular conversation costs (Sonnet pricing)
        conversation_cost = (
            (self.total_input_tokens / 1_000_000 * 3.0) +
            (self.total_output_tokens / 1_000_000 * 15.0)
        )

        # Document processing costs (Haiku pricing - used for chunk summarization)
        doc_processing_cost = (
            (self.doc_processing_input_tokens / 1_000_000 * 0.25) +
            (self.doc_processing_output_tokens / 1_000_000 * 1.25)
        )

        # Vision API costs (Sonnet pricing - same as conversation)
        vision_cost = (
            (self.vision_input_tokens / 1_000_000 * 3.0) +
            (self.vision_output_tokens / 1_000_000 * 15.0)
        )

        total_cost = conversation_cost + doc_processing_cost + vision_cost

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
            # Document processing stats
            "doc_processing_count": self.doc_processing_count,
            "doc_processing_input_tokens": self.doc_processing_input_tokens,
            "doc_processing_output_tokens": self.doc_processing_output_tokens,
            "doc_processing_total_tokens": self.doc_processing_input_tokens + self.doc_processing_output_tokens,
            "doc_processing_cost": doc_processing_cost,
            "doc_processing_input_cost": self.doc_processing_input_tokens / 1_000_000 * 0.25,
            "doc_processing_output_cost": self.doc_processing_output_tokens / 1_000_000 * 1.25,
            # Vision API stats
            "vision_image_count": self.vision_image_count,
            "vision_input_tokens": self.vision_input_tokens,
            "vision_output_tokens": self.vision_output_tokens,
            "vision_total_tokens": self.vision_input_tokens + self.vision_output_tokens,
            "vision_cost": vision_cost,
            "vision_input_cost": self.vision_input_tokens / 1_000_000 * 3.0,
            "vision_output_cost": self.vision_output_tokens / 1_000_000 * 15.0,
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
        # Phase 5.9: Skip history token estimation - pydantic-ai tracks actual usage
        history_tokens = 0
        # Note: conversation_history now contains pydantic-ai ModelMessage objects
        # Token estimation for these is complex and the API provides actual counts

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
