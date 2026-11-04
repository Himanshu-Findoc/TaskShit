from datetime import datetime

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from config import (
    PROJECTS, COMMITS_LIMIT, PROJECT_SPRINT_MAP, CATEGORIES, LABEL_OPTIONS,
)
from git_service import get_commits
from helpers import sort_commits
from ai_service import generate_ai_task, generate_meeting_task
from nexus_service import submit_task
from sprintsheet_service import submit_sprintsheet

console = Console()

QSTYLE = questionary.Style([
    ("qmark", "fg:#00ff9f bold"), ("question", "bold fg:#00d4ff"),
    ("answer", "fg:#00ff9f bold"), ("pointer", "fg:#ff6b6b bold"),
    ("highlighted", "fg:#00ff9f bold"), ("selected", "fg:#00ff9f"),
    ("separator", "fg:#444466 bold"),
])


def load_commits():
    all_commits = []
    for repo_path in PROJECTS:
        try:
            all_commits.extend(get_commits(repo_path, COMMITS_LIMIT))
        except Exception as e:
            console.print(f"[red]Error:[/red] {repo_path}: {e}")
    grouped = {}
    for c in sort_commits(all_commits):
        grouped.setdefault(c["repo"], []).append(c)
    return grouped


def select_commits(grouped):
    choices = []
    for repo, commits in grouped.items():
        choices.append(questionary.Separator(f"  ━━━  {repo.upper()}  ━━━"))
        for c in commits:
            choices.append(questionary.Choice(
                title=f"  {c['message'][:60]}  [{c['hash']}]  • {c['date']}",
                value=c,
            ))
    return questionary.checkbox(
        "Select commits", choices=choices, style=QSTYLE,
    ).ask() or []


def ask_date():
    while True:
        raw = questionary.text(
            "Start/Due date (DD-MM-YYYY):",
            default=datetime.now().strftime("%d-%m-%Y"), style=QSTYLE,
        ).ask().strip()
        try:
            return datetime.strptime(raw, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            console.print("[yellow]⚠ Use DD-MM-YYYY[/yellow]")


def ask_labels():
    return questionary.checkbox(
        "Labels (space to select, enter to confirm):",
        choices=LABEL_OPTIONS, style=QSTYLE,
    ).ask() or []


def ask_hours(label):
    while True:
        raw = questionary.text(label, default="1", style=QSTYLE).ask().strip()
        try:
            if float(raw) > 0:
                return raw
        except ValueError:
            pass
        console.print("[yellow]⚠ Enter a positive number, e.g. 1.5[/yellow]")


def ask_time():
    while True:
        raw = questionary.text(
            "Start time (H:MM AM/PM):",
            default=datetime.now().strftime("%I:%M %p").lstrip("0"), style=QSTYLE,
        ).ask().strip().upper()
        try:
            return datetime.strptime(raw, "%I:%M %p").strftime("%I:%M %p").lstrip("0")
        except ValueError:
            console.print("[yellow]⚠ Use H:MM AM/PM, e.g. 3:30 PM[/yellow]")


def ask_category():
    return questionary.select(
        "Task type:", choices=list(CATEGORIES), style=QSTYLE,
    ).ask()


def ask_sprint(selected):
    sprints = {PROJECT_SPRINT_MAP.get(c["repo"]) for c in selected} - {None}
    if len(sprints) == 1:
        return sprints.pop()
    return questionary.select(
        "Pick sprint:",
        choices=["FinDost Features", "FinZoom Live"], style=QSTYLE,
    ).ask()


def main():
    console.print(Panel.fit("[bold cyan]⚡ Git Commits → Nexus Task[/bold cyan]"))
    grouped = load_commits()

    while True:
        category = ask_category()
        prefix, repo_filter = CATEGORIES[category]
        selected = []

        if repo_filter is None:  # Meeting
            agenda = questionary.text(
                "Meeting agenda (Esc+Enter to finish):", multiline=True, style=QSTYLE,
            ).ask() or ""
            if not agenda.strip():
                console.print("[yellow]⚠ Agenda is empty.[/yellow]")
                proceed = False
            else:
                proceed = True
        else:
            filtered = {r: c for r, c in grouped.items() if repo_filter(r)}
            if not filtered:
                console.print(f"[yellow]⚠ No repos found for {category}.[/yellow]")
                proceed = False
            else:
                selected = select_commits(filtered)
                proceed = bool(selected)
                if not selected:
                    console.print("[yellow]⚠ No commits selected.[/yellow]")
                else:
                    tree = Tree("[bold green]✅ Selected[/bold green]")
                    for c in selected:
                        tree.add(f"[cyan]{c['repo']}[/cyan] → {c['message']}")
                    console.print(tree)

        if proceed:
            sprint = ask_sprint(selected)
            labels = ask_labels()
            date_iso = ask_date()
            targets = questionary.select(
                "Upload to:",
                choices=["Nexus + Sprint sheet", "Nexus only", "Sprint sheet only"],
                style=QSTYLE,
            ).ask()
            to_nexus = "Nexus" in targets
            to_sheet = "Sprint" in targets
            if to_sheet:
                hours = ask_hours(
                    "Meeting duration in hours (e.g. 0.5):" if not selected
                    else "Estimated hours (e.g. 2.25):"
                )
                start_time = ask_time()

            console.print("[magenta]🤖 Generating title & description...[/magenta]")
            if selected:
                title, description = generate_ai_task(selected)
            else:
                title, description = generate_meeting_task(agenda)

            title = questionary.text(
                f"Summary ({prefix} is added automatically):", default=title, style=QSTYLE,
            ).ask().strip()
            title = f"{prefix} {title}"[:150]
            console.print(Panel(description, title="Description", border_style="green"))
            if questionary.confirm("Edit description?", default=False, style=QSTYLE).ask():
                description = questionary.text(
                    "Description (Esc+Enter to finish):",
                    default=description, multiline=True, style=QSTYLE,
                ).ask()

            console.print(
                f"Summary: [bold]{title}[/bold]\n"
                f"Sprint: [bold]{sprint}[/bold] | Labels: {labels or '-'} | Date: {date_iso}"
            )
            if questionary.confirm(f"Upload to {targets}?", default=True, style=QSTYLE).ask():
                if to_nexus:
                    console.print("[cyan]→ Nexus...[/cyan]")
                    ok = submit_task(title, description, selected, labels, date_iso, sprint)
                    console.print("[bold green]✅ Nexus done[/bold green]" if ok
                                  else "[bold red]❌ Nexus failed[/bold red]")
                if to_sheet:
                    console.print("[cyan]→ Sprint sheet...[/cyan]")
                    sp_date = datetime.strptime(date_iso, "%Y-%m-%d")
                    ok = submit_sprintsheet(
                        title, description, selected, hours,
                        f"{sp_date.month}/{sp_date.day}/{sp_date.year}", start_time,
                    )
                    console.print("[bold green]✅ Sprint sheet done[/bold green]" if ok
                                  else "[bold red]❌ Sprint sheet failed[/bold red]")

        if not questionary.confirm("Create another task?", default=True, style=QSTYLE).ask():
            break


if __name__ == "__main__":
    main()
