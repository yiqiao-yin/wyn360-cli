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
