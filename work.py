#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


RDE_DIR = Path.home() / "rde"
PROJECTS_FILE = RDE_DIR / "projects.yaml"

ROLES = ("shell", "claude", "cursor", "git")

ROLE_COMMANDS = {
    "claude": """
if command -v claude >/dev/null 2>&1; then
    claude
else
    echo "Claude Code is niet gevonden."
    echo "Controleer de installatie en je PATH."
fi

exec bash
""",
    "cursor": """
if command -v agent >/dev/null 2>&1; then
    agent
else
    echo "Cursor Agent is niet gevonden."
    echo "Controleer de installatie en je PATH."
fi

exec bash
""",
    "git": """
if command -v lazygit >/dev/null 2>&1; then
    lazygit
else
    echo "Lazygit is niet gevonden."
    echo "Controleer de installatie en je PATH."
fi

exec bash
""",
}


def run(
    command: list[str],
    *,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Voer een extern commando uit."""
    return subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def resolve_path(raw_path: str) -> Path:
    """Werk ~ en omgevingsvariabelen in een pad uit."""
    return Path(
        os.path.expandvars(raw_path)
    ).expanduser().resolve()


def discover_projects(root: Path, depth: int) -> dict[str, Path]:
    """Zoek projectmappen onder een opgegeven hoofdmap."""
    projects: dict[str, Path] = {}

    if not root.is_dir():
        return projects

    if depth <= 1:
        candidates = [
            path
            for path in root.iterdir()
            if path.is_dir()
        ]
    else:
        candidates = [
            path
            for path in root.rglob("*")
            if path.is_dir()
            and len(path.relative_to(root).parts) == depth
        ]

    for path in sorted(candidates):
        if path.name.startswith("."):
            continue

        projects[path.name] = path

    return projects


def load_projects() -> dict[str, Path]:
    """Lees vaste projecten en automatisch te doorzoeken hoofdmappen."""
    if not PROJECTS_FILE.exists():
        raise FileNotFoundError(
            f"Projectbestand ontbreekt: {PROJECTS_FILE}"
        )

    with PROJECTS_FILE.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = yaml.safe_load(file) or {}

    projects: dict[str, Path] = {}

    # Handmatig vastgelegde projecten.
    for name, settings in (data.get("projects") or {}).items():
        raw_path = settings.get("path")

        if raw_path:
            projects[name] = resolve_path(raw_path)

    # Automatisch gevonden projecten.
    for settings in data.get("roots") or []:
        raw_path = settings.get("path")

        if not raw_path:
            continue

        root = resolve_path(raw_path)
        depth = int(settings.get("depth", 1))

        for name, path in discover_projects(root, depth).items():
            display_name = name

            if display_name in projects:
                display_name = f"{name} [{root.name}]"

            projects[display_name] = path

    return dict(
        sorted(
            projects.items(),
            key=lambda item: item[0].lower(),
        )
    )


def choose_project(
    projects: dict[str, Path],
    search_term: str | None,
) -> tuple[str, Path]:
    """Kies via een zoekterm of via fzf één project."""
    if not projects:
        raise RuntimeError("Er zijn geen projecten gevonden.")

    if search_term:
        matches = {
            name: path
            for name, path in projects.items()
            if search_term.lower() in name.lower()
        }

        if len(matches) == 1:
            return next(iter(matches.items()))

        if not matches:
            raise RuntimeError(
                f"Geen project gevonden voor: {search_term}"
            )

        candidates = matches
    else:
        candidates = projects

    result = subprocess.run(
        [
            "fzf",
            "--prompt=Project: ",
            "--height=70%",
            "--reverse",
            "--border",
        ],
        input="\n".join(candidates),
        text=True,
        capture_output=True,
        check=False,
    )

    selected_name = result.stdout.strip()

    if not selected_name:
        raise KeyboardInterrupt

    return selected_name, candidates[selected_name]


def tmux_window_names() -> set[str]:
    """Geef alle bestaande tmux-windownamen terug."""
    result = run(
        [
            "tmux",
            "list-windows",
            "-F",
            "#{window_name}",
        ],
        check=False,
        capture_output=True,
    )

    return set(result.stdout.splitlines())


def safe_project_name(name: str) -> str:
    """Maak een korte en bruikbare projectnaam voor tmux."""
    safe_name = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        name,
    ).strip("_")

    return safe_name[:40] or "project"


def create_window(
    *,
    project_name: str,
    role: str,
    path: Path,
    existing_windows: set[str],
) -> None:
    """Maak een tmux-window aan wanneer het nog niet bestaat."""
    window_name = f"{project_name}-{role}"

    if window_name in existing_windows:
        return

    command = [
        "tmux",
        "new-window",
        "-d",
        "-n",
        window_name,
        "-c",
        str(path),
    ]

    role_command = ROLE_COMMANDS.get(role)

    if role_command:
        shell_command = (
            "bash -ic "
            + shlex.quote(role_command.strip())
        )
        command.append(shell_command)

    run(command)


def open_project_workspace(name: str, path: Path) -> None:
    """
    Maak of hergebruik de vier vaste projectwindows:

    - project-shell
    - project-claude
    - project-cursor
    - project-git
    """
    if not os.environ.get("TMUX"):
        raise RuntimeError(
            "Start 'work' vanuit tmux."
        )

    project_name = safe_project_name(name)
    existing_windows = tmux_window_names()

    for role in ROLES:
        create_window(
            project_name=project_name,
            role=role,
            path=path,
            existing_windows=existing_windows,
        )

    # Bewaar het momenteel gekozen project voor de Alt-sneltoetsen.
    run(
        [
            "tmux",
            "set-option",
            "-g",
            "@rde_active_project",
            project_name,
        ]
    )

    # Begin standaard in de projectshell.
    run(
        [
            "tmux",
            "select-window",
            "-t",
            f":{project_name}-shell",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Open een permanente tmux-werkplek "
            "met shell, Claude, Cursor en Git."
        )
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="Volledige of gedeeltelijke projectnaam.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Toon alle gevonden projecten.",
    )
    args = parser.parse_args()

    try:
        projects = load_projects()

        if args.list:
            for name, path in projects.items():
                status = "" if path.is_dir() else " [PAD ONTBREEKT]"
                print(f"{name:35} {path}{status}")

            return 0

        name, path = choose_project(
            projects,
            args.project,
        )

        if not path.is_dir():
            raise FileNotFoundError(
                f"De projectmap bestaat niet: {path}"
            )

        open_project_workspace(name, path)

    except KeyboardInterrupt:
        return 0
    except (FileNotFoundError, RuntimeError) as error:
        print(f"Fout: {error}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(
            f"Commando mislukt: {' '.join(error.cmd)}",
            file=sys.stderr,
        )
        return error.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
