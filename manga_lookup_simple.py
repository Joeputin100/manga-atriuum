#!/usr/bin/env python3
"""
Simple Manga Lookup Tool - Basic Working Version
"""

import os
import json
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich import print as rprint

# Load environment variables
load_dotenv()

def correct_series_name(series_name: str) -> list:
    """Use DeepSeek API to correct and suggest manga series names"""
    api_key = os.getenv("DEEPSEEK_API_KEY")

    prompt = f"""
    Given the manga series name "{series_name}", provide 3-5 corrected or alternative names
    that are actual manga series. Return only the names as a JSON list, no additional text.

    Example format: ["One Piece", "Naruto", "Bleach"]
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.3
    }

    try:
        response = requests.post("https://api.deepseek.com/v1/chat/completions",
                               headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON response
        suggestions = json.loads(content)
        return suggestions

    except Exception as e:
        rprint(f"[red]Error using DeepSeek API: {e}[/red]")
        return [series_name]  # Fallback to original name

def main():
    """Main function to run the manga lookup tool"""
    console = Console()

    rprint("[bold blue]Manga Lookup Tool[/bold blue]")

    try:
        # Get user input
        series_name = Prompt.ask("\n[bold]Enter manga series name[/bold]")
        start_volume = IntPrompt.ask("[bold]Enter start volume[/bold]", default=1)
        end_volume = IntPrompt.ask("[bold]Enter end volume[/bold]", default=start_volume)

        # Correct series name using DeepSeek API
        rprint("\n[cyan]Correcting series name with DeepSeek API...[/cyan]")
        suggestions = correct_series_name(series_name)

        if len(suggestions) > 1:
            rprint("\n[bold]Please select the correct series name:[/bold]")
            for i, suggestion in enumerate(suggestions, 1):
                rprint(f"{i}. {suggestion}")

            choice = IntPrompt.ask("\nSelect option", choices=[str(i) for i in range(1, len(suggestions) + 1)])
            selected_series = suggestions[choice - 1]
        else:
            selected_series = suggestions[0]

        rprint(f"\n[green]Using series: {selected_series}[/green]")
        rprint(f"[green]Volume range: {start_volume} to {end_volume}[/green]")
        rprint("\n[cyan]Basic functionality working![/cyan]")

    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        rprint(f"\n[red]An error occurred: {e}[/red]")

if __name__ == "__main__":
    main()