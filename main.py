"""
Interactive CLI Chat Interface for CrewAI Conversational RAG.
Features Rich terminal styling, session memory controls, and knowledge inspection.
"""

import sys
import os
import argparse

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from crew import ConversationalRAGCrew
from tools import ListKnowledgeDocumentsTool

console = Console(force_terminal=True)

def print_banner():
    banner_text = """
[bold cyan]╔═══════════════════════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]  [bold yellow]🤖 CrewAI Conversational Multi-Agent RAG System[/bold yellow]                         [bold cyan]║[/bold cyan]
[bold cyan]║[/bold cyan]  [white]Tri-Agent Team: Retriever + Aggregator Host Specialist + Synthesizer[/white]     [bold cyan]║[/bold cyan]
[bold cyan]╚═══════════════════════════════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner_text)
    console.print("[dim]Type your message to chat, or use commands: [bold]/help[/bold], [bold]/docs[/bold], [bold]/clear[/bold], [bold]/exit[/bold][/dim]\n")

def show_help():
    table = Table(title="Available Chat Commands", show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan", width=12)
    table.add_column("Description", style="white")
    table.add_row("/docs", "List all documents and files currently in the knowledge base")
    table.add_row("/clear", "Reset the conversation memory history")
    table.add_row("/status", "Display active model, memory turns, and configuration")
    table.add_row("/help", "Show this help table")
    table.add_row("/exit", "Exit the chat session")
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="CrewAI Conversational RAG CLI")
    parser.add_argument("--test", type=str, help="Run a single test query non-interactively")
    args = parser.parse_args()

    crew = ConversationalRAGCrew(verbose=True)

    if args.test:
        console.print(f"[bold green]Running test query:[/bold green] {args.test}")
        response = crew.ask(args.test)
        console.print(Panel(Markdown(response), title="Agent Response", border_style="cyan"))
        return

    print_banner()

    # Inform status
    if not crew.api_key:
        console.print(
            Panel(
                "[bold yellow]⚠️ No API Key Detected in .env[/bold yellow]\n\n"
                "Please configure [cyan]GEMINI_API_KEY[/cyan] (or [cyan]OPENAI_API_KEY[/cyan]) in `.env`.\n"
                "You can still inspect documents using [bold]/docs[/bold]!",
                title="Configuration Notice",
                border_style="yellow"
            )
        )
    else:
        console.print(f"[green]✓[/green] Active LLM: [bold]{crew.model}[/bold]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
            if not user_input:
                continue

            if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                console.print("[cyan]Goodbye! Have a great day.[/cyan]")
                break
            elif user_input.lower() == "/help":
                show_help()
                continue
            elif user_input.lower() == "/docs":
                docs_info = ListKnowledgeDocumentsTool()._run()
                console.print(Panel(Markdown(docs_info), title="Knowledge Base Index", border_style="blue"))
                continue
            elif user_input.lower() == "/clear":
                crew.clear_memory()
                console.print("[yellow]Conversation memory has been cleared.[/yellow]\n")
                continue
            elif user_input.lower() == "/status":
                turns = len(crew.chat_history) // 2
                console.print(f"[cyan]Active Model:[/cyan] {crew.model}")
                console.print(f"[cyan]Conversation Memory:[/cyan] {turns} turns recorded")
                console.print(f"[cyan]API Key Loaded:[/cyan] {'Yes' if crew.api_key else 'No'}\n")
                continue

            with console.status("[bold cyan]Agents are collaborating and searching knowledge base...[/bold cyan]", spinner="dots"):
                response = crew.ask(user_input)

            console.print(Panel(Markdown(response), title="🤖 CrewAI Assistant", border_style="cyan"))
            console.print()

        except (KeyboardInterrupt, EOFError):
            console.print("\n[cyan]Session ended.[/cyan]")
            break

if __name__ == "__main__":
    main()
