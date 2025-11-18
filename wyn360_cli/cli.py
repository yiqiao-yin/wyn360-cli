"""WYN360 CLI - Command-line interface for the coding assistant"""

import click
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from .agent import WYN360Agent
from .config import load_config, get_user_config_path, get_project_config_path
import shutil

# Get terminal width, with fallback to 120 if detection fails
terminal_width = shutil.get_terminal_size(fallback=(120, 24)).columns
# Ensure minimum width of 80, maximum of 200 for readability
console_width = max(80, min(200, terminal_width))
console = Console(width=console_width, force_terminal=True)


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option(
    '--api-key',
    default=None,
    help='Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.'
)
@click.option(
    '--model',
    default='claude-sonnet-4-20250514',
    help='Claude model to use (default: claude-sonnet-4-20250514)'
)
@click.option(
    '--max-internet-search-limit',
    default=None,
    type=int,
    help='Maximum number of web searches per session (default: 5). Use MAX_INTERNET_SEARCH_LIMIT env var or this flag.'
)
@click.option(
    '--max-token',
    default=None,
    type=int,
    help='Maximum tokens for model output (default: 4096). Use MAX_TOKEN env var or this flag.'
)
def main(api_key, model, max_internet_search_limit, max_token):
    """
    WYN360 - An intelligent AI coding assistant CLI tool.

    Interact with Claude to build projects, generate code, and improve your codebase.

    \b
    QUICK START:
      $ export ANTHROPIC_API_KEY=your_api_key
      $ wyn360
      You: Create a Streamlit chatbot
      WYN360: [Generates complete app.py with code]

    \b
    SLASH COMMANDS (use inside session):
      /clear          Clear conversation history and reset metrics
      /history        Show conversation history
      /save <file>    Save session to JSON file
      /load <file>    Load previous session
      /tokens         Show token usage and costs
      /stats          Show performance metrics (NEW in v0.3.19!)
      /model [name]   Show/switch AI model (haiku/sonnet/opus)
      /config         Show current configuration
      /help           Show detailed help inside session

    \b
    AVAILABLE TOOLS (AI can use automatically):
      File Operations:
        - read_file, write_file, list_files, delete_file, move_file
        - create_directory, get_project_info

      Code Operations:
        - execute_command (run scripts, install packages)
        - search_files (grep code patterns)
        - generate_tests (auto-generate pytest tests)

      Git Operations:
        - git_status, git_diff, git_log, git_branch

      HuggingFace Integration:
        - check_hf_authentication, authenticate_hf
        - create_hf_readme, create_hf_space, push_to_hf_space

      GitHub Integration (NEW in v0.3.23):
        - check_gh_authentication, authenticate_gh
        - gh_commit_changes (commit and push to GitHub)
        - gh_create_pr (create pull requests)
        - gh_create_branch, gh_checkout_branch (branch management)
        - gh_merge_branch (merge branches)

      Web Search (NEW in v0.3.21):
        - web_search (weather, URLs, current info)
        - Real-time internet access with proper citations
        - Limited to 5 searches per session ($0.01 per search)

    \b
    EXAMPLES:
      # Start with different models
      $ wyn360 --model haiku              # Fast & cheap
      $ wyn360 --model sonnet             # Balanced (default)
      $ wyn360 --model opus               # Most capable

      # Quick commands
      $ wyn360 --api-key sk-ant-...       # Provide API key directly

    \b
    DOCUMENTATION:
      PyPI:        https://pypi.org/project/wyn360-cli/
      GitHub:      https://github.com/yiqiao-yin/wyn360-cli
      Use Cases:   See USE_CASES.md for detailed examples
      Get API Key: https://console.anthropic.com/

    Version: 0.3.23
    """
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Check if Bedrock mode is enabled
    use_bedrock = os.getenv('CLAUDE_CODE_USE_BEDROCK', '0') == '1'

    # Get API key from parameter or environment (not needed for Bedrock)
    api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

    # Get max internet search limit from parameter or environment (default: 5)
    # Priority: 1. CLI argument, 2. Environment variable, 3. Default (5)
    if max_internet_search_limit is None:
        max_internet_search_limit = int(os.getenv('MAX_INTERNET_SEARCH_LIMIT', '5'))
    # Ensure it's a positive integer
    if max_internet_search_limit < 1:
        max_internet_search_limit = 5

    # Get max token from parameter or environment (default: 4096)
    # Priority: 1. CLI argument, 2. Environment variable, 3. Default (4096)
    if max_token is None:
        max_token = int(os.getenv('MAX_TOKEN', '4096'))
    # Ensure it's a positive integer
    if max_token < 1:
        max_token = 4096

    # Validate credentials based on mode
    if not use_bedrock and not api_key:
        raise click.UsageError(
            "API key is required when not using AWS Bedrock.\n\n"
            "Options:\n"
            "  1. Set Anthropic API key: export ANTHROPIC_API_KEY=sk-ant-xxx\n"
            "  2. Use AWS Bedrock: export CLAUDE_CODE_USE_BEDROCK=1\n"
            "     (requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)\n\n"
            "Get Anthropic API key from: https://console.anthropic.com/"
        )

    # Print banner
    print("""
██╗    ██╗██╗   ██╗███╗   ██╗██████╗  ██████╗  ██████╗
██║    ██║╚██╗ ██╔╝████╗  ██║╚════██╗██╔════╝ ██╔═████╗
██║ █╗ ██║ ╚████╔╝ ██╔██╗ ██║ █████╔╝███████╗ ██║██╔██║
██║███╗██║  ╚██╔╝  ██║╚██╗██║ ╚═══██╗██╔═══██╗████╔╝██║
╚███╔███╔╝   ██║   ██║ ╚████║██████╔╝╚██████╔╝╚██████╔╝
 ╚══╝╚══╝    ╚═╝   ╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚═════╝
    """)

    console.print(
        "[bold cyan]Your AI Coding Assistant[/bold cyan] - Powered by Anthropic Claude",
        justify="center"
    )
    console.print()
    console.print("[yellow]Commands:[/yellow]")
    console.print("  • Type your request to chat with the assistant")
    console.print("  • Press [bold]Enter[/bold] to submit, [bold]Ctrl+Enter[/bold] for new line")
    console.print("  • Type [bold]'exit'[/bold] or [bold]'quit'[/bold] to end the session")
    console.print()
    console.print("[yellow]Note:[/yellow] You'll be asked to confirm before executing any commands")
    console.print()

    # Load configuration
    config = load_config()

    # Override max_tokens from CLI or environment variable
    # Priority: CLI arg > env var > config file > default (4096)
    config.max_tokens = max_token

    # Show config status
    user_config_path = get_user_config_path()
    project_config_path = get_project_config_path()

    if user_config_path.exists():
        console.print(f"[dim]• Loaded user config from: {user_config_path}[/dim]")
    if project_config_path:
        console.print(f"[dim]• Loaded project config from: {project_config_path}[/dim]")

    # Initialize agent with config
    try:
        # Use model from CLI arg if provided, otherwise use config model
        if model != 'claude-sonnet-4-20250514':  # If user specified a different model
            agent = WYN360Agent(api_key=api_key, model=model, config=config, use_bedrock=use_bedrock, max_search_limit=max_internet_search_limit)
        else:
            agent = WYN360Agent(api_key=api_key, config=config, use_bedrock=use_bedrock, max_search_limit=max_internet_search_limit)

        actual_model = agent.model_name

        # Show connection status
        if use_bedrock:
            # Bedrock mode already prints status in agent.__init__
            pass
        else:
            console.print(f"[green]✓[/green] Connected using model: [cyan]{actual_model}[/cyan]")

        # Show custom instructions indicator
        if config.custom_instructions:
            console.print("[dim]• Custom instructions loaded[/dim]")
        if config.project_context:
            console.print("[dim]• Project context loaded[/dim]")

        console.print()
    except Exception as e:
        console.print(f"[red]Error initializing agent:[/red] {str(e)}")
        return

    # Main chat loop
    asyncio.run(chat_loop(agent))


def handle_slash_command(command: str, agent: WYN360Agent) -> tuple[bool, str]:
    """
    Handle slash commands.

    Args:
        command: The slash command (without the /)
        agent: The WYN360Agent instance

    Returns:
        Tuple of (handled: bool, message: str)
    """
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None

    if cmd == "clear":
        agent.clear_history()
        return True, "✓ Conversation history cleared. Token counters reset."

    elif cmd == "history":
        history = agent.get_history()
        if not history:
            return True, "No conversation history yet."

        from rich.table import Table
        table = Table(title="Conversation History", show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Role", style="magenta", width=10)
        table.add_column("Content", style="white")

        for idx, msg in enumerate(history, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # Truncate long messages
            if len(content) > 200:
                content = content[:200] + "..."
            table.add_row(str(idx), role, content)

        console.print(table)
        return True, ""

    elif cmd == "save":
        if not arg:
            return True, "❌ Usage: /save <filename>\nExample: /save my_session.json"

        success = agent.save_session(arg)
        if success:
            return True, f"✓ Session saved to: {arg}"
        else:
            return True, f"❌ Failed to save session to: {arg}"

    elif cmd == "load":
        if not arg:
            return True, "❌ Usage: /load <filename>\nExample: /load my_session.json"

        success = agent.load_session(arg)
        if success:
            return True, f"✓ Session loaded from: {arg}"
        else:
            return True, f"❌ Failed to load session from: {arg}"

    elif cmd == "tokens":
        stats = agent.get_token_stats()

        from rich.table import Table
        from rich.panel import Panel

        table = Table(title="Token Usage Statistics", show_header=False)
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="yellow")

        table.add_row("Total Requests", str(stats["total_requests"]))
        table.add_row("─" * 30, "─" * 20)
        table.add_row("Input Tokens", f"{stats['total_input_tokens']:,}")
        table.add_row("Output Tokens", f"{stats['total_output_tokens']:,}")
        table.add_row("Total Tokens", f"{stats['total_tokens']:,}")
        table.add_row("─" * 30, "─" * 20)
        table.add_row("Input Cost", f"${stats['input_cost']:.4f}")
        table.add_row("Output Cost", f"${stats['output_cost']:.4f}")
        table.add_row("Subtotal (Conversation)", f"${stats['input_cost'] + stats['output_cost']:.4f}")

        # Add document processing stats if any
        if stats["doc_processing_count"] > 0:
            table.add_row("─" * 30, "─" * 20)
            table.add_row("[bold]Document Processing[/bold]", "")
            table.add_row("  Chunks Processed", str(stats["doc_processing_count"]))
            table.add_row("  Input Tokens", f"{stats['doc_processing_input_tokens']:,}")
            table.add_row("  Output Tokens", f"{stats['doc_processing_output_tokens']:,}")
            table.add_row("  Total Tokens", f"{stats['doc_processing_total_tokens']:,}")
            table.add_row("  Input Cost (Haiku)", f"${stats['doc_processing_input_cost']:.4f}")
            table.add_row("  Output Cost (Haiku)", f"${stats['doc_processing_output_cost']:.4f}")
            table.add_row("  Subtotal (Documents)", f"${stats['doc_processing_cost']:.4f}")

        # Add vision API stats if any
        if stats["vision_image_count"] > 0:
            table.add_row("─" * 30, "─" * 20)
            table.add_row("[bold]Vision API[/bold]", "")
            table.add_row("  Images Processed", str(stats["vision_image_count"]))
            table.add_row("  Input Tokens", f"{stats['vision_input_tokens']:,}")
            table.add_row("  Output Tokens", f"{stats['vision_output_tokens']:,}")
            table.add_row("  Total Tokens", f"{stats['vision_total_tokens']:,}")
            table.add_row("  Input Cost (Sonnet)", f"${stats['vision_input_cost']:.4f}")
            table.add_row("  Output Cost (Sonnet)", f"${stats['vision_output_cost']:.4f}")
            table.add_row("  Subtotal (Vision)", f"${stats['vision_cost']:.4f}")

        table.add_row("─" * 30, "─" * 20)
        table.add_row("[bold]Total Cost[/bold]", f"[bold]${stats['total_cost']:.4f}[/bold]")
        table.add_row("─" * 30, "─" * 20)
        table.add_row("Avg Cost/Request", f"${stats['avg_cost_per_request']:.4f}")

        console.print(table)
        return True, ""

    elif cmd == "stats":
        # Get both token stats and performance stats
        token_stats = agent.get_token_stats()
        perf_stats = agent.get_performance_stats()

        from rich.table import Table
        from rich.panel import Panel
        from rich.columns import Columns

        # Token Usage Table
        token_table = Table(title="Token Usage", show_header=False)
        token_table.add_column("Metric", style="cyan")
        token_table.add_column("Value", style="yellow")

        token_table.add_row("Total Requests", str(token_stats["total_requests"]))
        token_table.add_row("Input Tokens", f"{token_stats['total_input_tokens']:,}")
        token_table.add_row("Output Tokens", f"{token_stats['total_output_tokens']:,}")
        token_table.add_row("Total Cost", f"${token_stats['total_cost']:.4f}")

        # Performance Table
        perf_table = Table(title="Performance Metrics", show_header=False)
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", style="yellow")

        # Session duration
        duration = perf_stats["session_duration_seconds"]
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"

        perf_table.add_row("Session Duration", duration_str)
        perf_table.add_row("Avg Response Time", f"{perf_stats['avg_response_time']:.2f}s")
        perf_table.add_row("Min Response Time", f"{perf_stats['min_response_time']:.2f}s")
        perf_table.add_row("Max Response Time", f"{perf_stats['max_response_time']:.2f}s")
        perf_table.add_row("Error Count", str(perf_stats['error_count']))

        # Tool Usage Table
        tool_table = Table(title="Tool Usage", show_header=False)
        tool_table.add_column("Metric", style="cyan")
        tool_table.add_column("Value", style="yellow")

        tool_table.add_row("Total Tool Calls", str(perf_stats['total_tool_calls']))
        tool_table.add_row("Successful Calls", str(perf_stats['successful_tool_calls']))
        tool_table.add_row("Failed Calls", str(perf_stats['failed_tool_calls']))
        tool_table.add_row("Success Rate", f"{perf_stats['tool_success_rate']:.1f}%")

        # Print all tables
        console.print()
        console.print(Columns([token_table, perf_table]))
        console.print()
        console.print(tool_table)

        # Show most used tools if any
        if perf_stats['most_used_tools']:
            console.print()
            tools_list = Table(title="Most Used Tools", show_header=True)
            tools_list.add_column("Tool", style="cyan")
            tools_list.add_column("Success", style="green")
            tools_list.add_column("Failed", style="red")
            tools_list.add_column("Total", style="yellow")

            for tool_name, stats in perf_stats['most_used_tools']:
                total = stats['success'] + stats['failed']
                tools_list.add_row(
                    tool_name,
                    str(stats['success']),
                    str(stats['failed']),
                    str(total)
                )

            console.print(tools_list)

        # Show error summary if any
        if perf_stats['error_types']:
            console.print()
            error_table = Table(title="Error Summary", show_header=True)
            error_table.add_column("Error Type", style="red")
            error_table.add_column("Count", style="yellow")

            for error_type, count in perf_stats['error_types'].items():
                error_table.add_row(error_type, str(count))

            console.print(error_table)

        return True, ""

    elif cmd == "model":
        if not arg:
            # Show current model info
            model_info = agent.get_model_info()

            from rich.table import Table
            from rich.panel import Panel

            table = Table(title="Current Model Information", show_header=False)
            table.add_column("Property", style="cyan", width=25)
            table.add_column("Value", style="yellow")

            table.add_row("Model", model_info["display_name"])
            table.add_row("Full ID", model_info["current_model"])
            table.add_row("Description", model_info["description"])
            table.add_row("─" * 25, "─" * 50)
            table.add_row("Input Cost", f"${model_info['input_cost_per_million']}/M tokens")
            table.add_row("Output Cost", f"${model_info['output_cost_per_million']}/M tokens")

            console.print(table)
            console.print("\n[yellow]Available models:[/yellow] haiku, sonnet, opus")
            console.print("[yellow]Usage:[/yellow] /model <name>  (e.g., /model haiku)")
            return True, ""
        else:
            # Switch to specified model
            model_name = arg.strip()
            success = agent.switch_model(model_name)

            if success:
                model_info = agent.get_model_info()
                return True, f"✓ Switched to {model_info['display_name']} ({model_info['current_model']})"
            else:
                return True, f"❌ Failed to switch to model: {model_name}"

    elif cmd == "config":
        # Show current configuration
        if not agent.config:
            return True, "No configuration loaded. Create ~/.wyn360/config.yaml or .wyn360.yaml"

        from rich.table import Table

        table = Table(title="Current Configuration", show_header=False)
        table.add_column("Setting", style="cyan", width=25)
        table.add_column("Value", style="yellow")

        # Model settings
        table.add_row("Model", agent.config.model)
        table.add_row("Max Tokens", str(agent.config.max_tokens))
        table.add_row("Temperature", str(agent.config.temperature))

        # Web search settings (only for Anthropic API mode)
        if not agent.use_bedrock:
            table.add_row("Max Internet Search", str(agent.max_search_limit))

        table.add_row("─" * 25, "─" * 50)

        # Config files
        if agent.config.user_config_path:
            table.add_row("User Config", agent.config.user_config_path)
        else:
            table.add_row("User Config", "[dim]Not found[/dim]")

        if agent.config.project_config_path:
            table.add_row("Project Config", agent.config.project_config_path)
        else:
            table.add_row("Project Config", "[dim]Not found[/dim]")

        table.add_row("─" * 25, "─" * 50)

        # Custom instructions
        if agent.config.custom_instructions:
            instructions_preview = agent.config.custom_instructions[:100] + "..." if len(agent.config.custom_instructions) > 100 else agent.config.custom_instructions
            table.add_row("Custom Instructions", instructions_preview)

        # Project context
        if agent.config.project_context:
            context_preview = agent.config.project_context[:100] + "..." if len(agent.config.project_context) > 100 else agent.config.project_context
            table.add_row("Project Context", context_preview)

        # Dependencies
        if agent.config.project_dependencies:
            deps = ", ".join(agent.config.project_dependencies[:5])
            if len(agent.config.project_dependencies) > 5:
                deps += f" (+{len(agent.config.project_dependencies) - 5} more)"
            table.add_row("Dependencies", deps)

        # Aliases
        if agent.config.aliases:
            aliases = ", ".join(list(agent.config.aliases.keys())[:3])
            if len(agent.config.aliases) > 3:
                aliases += f" (+{len(agent.config.aliases) - 3} more)"
            table.add_row("Aliases", aliases)

        console.print(table)
        console.print("\n[dim]Tip: Create ~/.wyn360/config.yaml for user settings[/dim]")
        console.print("[dim]Tip: Create .wyn360.yaml in project root for project settings[/dim]")
        return True, ""

    elif cmd == "help":
        help_text = """
[bold cyan]WYN360 CLI - Available Commands[/bold cyan]

[bold yellow]Chat Commands:[/bold yellow]
  • Type your request to chat with the assistant
  • Press [bold]Enter[/bold] to submit, [bold]Ctrl+Enter[/bold] for new line
  • Type [bold]exit[/bold] or [bold]quit[/bold] to end the session

[bold yellow]Slash Commands:[/bold yellow]
  [bold green]/clear[/bold green]            Clear conversation history and reset counters
  [bold green]/history[/bold green]          Show conversation history
  [bold green]/save <file>[/bold green]     Save session to JSON file
  [bold green]/load <file>[/bold green]     Load session from JSON file
  [bold green]/tokens[/bold green]           Show token usage statistics
  [bold green]/stats[/bold green]            Show comprehensive performance metrics
  [bold green]/model [name][/bold green]    Show/switch AI model (haiku/sonnet/opus)
  [bold green]/config[/bold green]           Show current configuration
  [bold green]/help[/bold green]             Show this help message

[bold yellow]Document Commands:[/bold yellow]
  [bold green]/set_doc_tokens <type> <n>[/bold green]  Set token limits (excel/word/pdf)
  [bold green]/clear_doc_cache [file][/bold green]     Clear document cache (all or specific)
  [bold green]/doc_cache_stats[/bold green]            Show document cache statistics
  [bold green]/set_image_mode <mode>[/bold green]      Image handling (skip/describe/vision)
  [bold green]/set_pdf_engine <engine>[/bold green]    PDF engine (pymupdf/pdfplumber)

[bold yellow]Examples:[/bold yellow]
  /save my_session.json       Save current conversation
  /load my_session.json       Continue previous conversation
  /tokens                     Check how much you've spent
  /stats                      View performance metrics and tool usage
  /model                      Show current model info
  /model haiku                Switch to Haiku (fast & cheap)
  /model opus                 Switch to Opus (most capable)
  /set_doc_tokens excel 15000 Set Excel token limit
  /doc_cache_stats            View cached documents
  /clear_doc_cache            Clear all document caches

[bold yellow]Tips:[/bold yellow]
  • Conversation history helps maintain context across turns
  • Use /clear if costs are getting high
  • Save important sessions for later reference
  • Token estimates are approximate (±10%)
  • Use /stats to monitor response times and tool performance
"""
        console.print(help_text)
        return True, ""

    elif cmd == "set_doc_tokens":
        # /set_doc_tokens <excel|word|pdf> <tokens>
        if not arg:
            return True, "❌ Usage: /set_doc_tokens <excel|word|pdf> <tokens>\nExample: /set_doc_tokens excel 15000"

        parts = arg.split()
        if len(parts) != 2:
            return True, "❌ Usage: /set_doc_tokens <excel|word|pdf> <tokens>\nExample: /set_doc_tokens excel 15000"

        doc_type = parts[0].lower()
        try:
            tokens = int(parts[1])
        except ValueError:
            return True, f"❌ Invalid token count: {parts[1]}. Must be a number."

        if doc_type not in ["excel", "word", "pdf"]:
            return True, f"❌ Invalid document type: {doc_type}. Use: excel, word, or pdf"

        if tokens < 1000 or tokens > 100000:
            return True, f"❌ Token count must be between 1,000 and 100,000"

        # Store in agent's config (we'll add this to agent later)
        if not hasattr(agent, 'doc_token_limits'):
            agent.doc_token_limits = {}
        agent.doc_token_limits[doc_type] = tokens

        return True, f"✓ {doc_type.title()} document token limit set to {tokens:,}"

    elif cmd == "clear_doc_cache":
        # /clear_doc_cache [file_path]
        from .document_readers import ChunkCache

        cache = ChunkCache()

        if arg:
            # Clear specific file
            file_path = arg.strip()
            count = cache.clear_cache(file_path)
            if count > 0:
                return True, f"✓ Cleared cache for: {file_path}"
            else:
                return True, f"❌ No cache found for: {file_path}"
        else:
            # Clear all
            count = cache.clear_cache()
            return True, f"✓ Cleared all document caches ({count} files deleted)"

    elif cmd == "doc_cache_stats":
        # /doc_cache_stats
        from .document_readers import ChunkCache
        from rich.table import Table

        cache = ChunkCache()
        stats = cache.get_stats()

        # Main stats table
        table = Table(title="📊 Document Cache Statistics", show_header=False)
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="yellow")

        table.add_row("Total Files Cached", str(stats["total_files"]))
        table.add_row("Total Chunks", str(stats["total_chunks"]))
        table.add_row("Total Cache Size", f"{stats['total_size_mb']} MB")
        table.add_row("Oldest Cache", stats["oldest_cache"])
        table.add_row("Newest Cache", stats["newest_cache"])

        console.print(table)

        # Cached files list
        if stats["cache_entries"]:
            console.print("\n[bold cyan]Cached Files:[/bold cyan]")
            files_table = Table(show_header=True)
            files_table.add_column("#", style="dim", width=4)
            files_table.add_column("File", style="white")
            files_table.add_column("Chunks", style="yellow", width=8)
            files_table.add_column("Age", style="green", width=15)

            for idx, entry in enumerate(stats["cache_entries"][:10], 1):  # Show top 10
                file_path = entry["file_path"]
                # Shorten path if too long
                if len(file_path) > 50:
                    file_path = "..." + file_path[-47:]

                files_table.add_row(
                    str(idx),
                    file_path,
                    str(entry["chunks"]),
                    entry["age_display"]
                )

            console.print(files_table)

            if len(stats["cache_entries"]) > 10:
                console.print(f"\n[dim]...and {len(stats['cache_entries']) - 10} more files[/dim]")

        return True, ""

    elif cmd == "set_image_mode":
        # /set_image_mode <skip|describe|vision>
        if not arg:
            # Show current mode
            current_mode = getattr(agent, 'image_handling_mode', 'describe')
            return True, f"Current image mode: {current_mode}\n\nAvailable modes:\n  skip     - Ignore images\n  describe - Extract alt text/captions (default)\n  vision   - Use Claude vision API (⚠️  increases costs)\n\nUsage: /set_image_mode <skip|describe|vision>"

        mode = arg.strip().lower()
        if mode not in ["skip", "describe", "vision"]:
            return True, f"❌ Invalid mode: {mode}. Use: skip, describe, or vision"

        agent.image_handling_mode = mode

        message = f"✓ Image handling mode set to: {mode}"
        if mode == "vision":
            message += "\n⚠️  Note: Vision mode will significantly increase API costs"

        return True, message

    elif cmd == "set_pdf_engine":
        # /set_pdf_engine <pymupdf|pdfplumber>
        if not arg:
            # Show current engine
            current_engine = getattr(agent, 'pdf_engine', 'pymupdf')
            return True, f"Current PDF engine: {current_engine}\n\nAvailable engines:\n  pymupdf     - Fast, general-purpose (default)\n  pdfplumber  - Better for complex tables\n\nUsage: /set_pdf_engine <pymupdf|pdfplumber>"

        engine = arg.strip().lower()
        if engine not in ["pymupdf", "pdfplumber"]:
            return True, f"❌ Invalid engine: {engine}. Use: pymupdf or pdfplumber"

        agent.pdf_engine = engine
        return True, f"✓ PDF engine set to: {engine}"

    else:
        return False, f"Unknown command: /{cmd}. Type /help for available commands."


async def chat_loop(agent: WYN360Agent):
    """
    Main interactive chat loop.

    Args:
        agent: The WYN360Agent instance
    """
    # Create key bindings for multi-line input
    # Ctrl+Enter = newline, Enter = submit
    kb = KeyBindings()

    @kb.add('c-j')  # Ctrl+Enter (Ctrl+J is the terminal code for Ctrl+Enter)
    def _(event):
        event.current_buffer.insert_text('\n')

    # Create prompt session
    session = PromptSession(
        multiline=False,
        key_bindings=kb,
        prompt_continuation=lambda width, line_number, is_soft_wrap: '... '
    )

    while True:
        try:
            # Get user input
            console.print("[bold green]You:[/bold green]")
            user_input = await session.prompt_async("")

            # Check for exit commands
            if user_input.lower().strip() in ['exit', 'quit', 'q']:
                console.print("\n[cyan]Goodbye! Happy coding! 👋[/cyan]")
                break

            # Skip empty input
            if not user_input.strip():
                continue

            # Check for slash commands
            if user_input.startswith('/'):
                command = user_input[1:]  # Remove the leading /
                handled, message = handle_slash_command(command, agent)
                if message:
                    console.print(f"[cyan]{message}[/cyan]")
                console.print()
                continue

            # Get complete response from agent
            console.print()

            # Show thinking status while agent processes
            with console.status("[bold blue]WYN360 is thinking...", spinner="dots"):
                # Get complete response (not streaming)
                response_text = await agent.chat_stream(user_input)

            # Now display the response word-by-word to simulate streaming
            console.print("[bold blue]WYN360:[/bold blue]")
            console.print()

            # Split response by spaces and print word-by-word
            import time
            words = response_text.split(' ')
            for i, word in enumerate(words):
                # Print word with space (except last word)
                if i < len(words) - 1:
                    console.print(word + ' ', end='', style="white")
                else:
                    console.print(word, end='', style="white")
                # Small delay to simulate streaming
                time.sleep(0.01)

            console.print()  # Add newline after printing
            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[cyan]Session interrupted. Goodbye! 👋[/cyan]")
            break
        except EOFError:
            console.print("\n\n[cyan]Goodbye! Happy coding! 👋[/cyan]")
            break
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {str(e)}\n")
            continue


if __name__ == '__main__':
    main()
