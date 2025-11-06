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

console = Console()


@click.command()
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
def main(api_key, model):
    """
    WYN360 - An intelligent AI coding assistant CLI tool.

    Interact with Claude to build projects, generate code, and improve your codebase.
    """
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Get API key from parameter or environment
    api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise click.UsageError(
            "API key is required. Provide via --api-key or set ANTHROPIC_API_KEY "
            "environment variable.\n\n"
            "Get your API key from: https://console.anthropic.com/"
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

    # Initialize agent
    try:
        agent = WYN360Agent(api_key=api_key, model=model)
        console.print(f"[green]✓[/green] Connected using model: [cyan]{model}[/cyan]")
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
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="yellow")

        table.add_row("Total Requests", str(stats["total_requests"]))
        table.add_row("─" * 25, "─" * 20)
        table.add_row("Input Tokens", f"{stats['total_input_tokens']:,}")
        table.add_row("Output Tokens", f"{stats['total_output_tokens']:,}")
        table.add_row("Total Tokens", f"{stats['total_tokens']:,}")
        table.add_row("─" * 25, "─" * 20)
        table.add_row("Input Cost", f"${stats['input_cost']:.4f}")
        table.add_row("Output Cost", f"${stats['output_cost']:.4f}")
        table.add_row("Total Cost", f"${stats['total_cost']:.4f}")
        table.add_row("─" * 25, "─" * 20)
        table.add_row("Avg Cost/Request", f"${stats['avg_cost_per_request']:.4f}")

        console.print(table)
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
  [bold green]/model [name][/bold green]    Show/switch AI model (haiku/sonnet/opus)
  [bold green]/help[/bold green]             Show this help message

[bold yellow]Examples:[/bold yellow]
  /save my_session.json       Save current conversation
  /load my_session.json       Continue previous conversation
  /tokens                     Check how much you've spent
  /model                      Show current model info
  /model haiku                Switch to Haiku (fast & cheap)
  /model opus                 Switch to Opus (most capable)

[bold yellow]Tips:[/bold yellow]
  • Conversation history helps maintain context across turns
  • Use /clear if costs are getting high
  • Save important sessions for later reference
  • Token estimates are approximate (±10%)
"""
        console.print(help_text)
        return True, ""

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

            # Get response from agent with progress indicator
            console.print()
            with console.status("[bold cyan]WYN360 is thinking...", spinner="dots"):
                response = await agent.chat(user_input)

            # Display response with markdown formatting
            console.print("[bold blue]WYN360:[/bold blue]")
            console.print()
            md = Markdown(response)
            console.print(md)
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
