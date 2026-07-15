#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml


RDE_DIR = Path.home() / "rde"
PROJECTS_FILE = RDE_DIR / "projects.yaml"


def run(
    command: list[str],
    *,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command with basic error handling."""
    return subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def load_projects() -> dict[str, Path]:
    if not PROJECTS_FILE.exists():
        raise FileNotFoundError(
            f"Projectbestand ontbreekt: {PROJECTS_FILE}"
        )

    with PROJECTS_FILE.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    raw_projects = data.get("projects", {})
    projects: dict[str, Path] = {}

    for name, settings in raw_projects.items():
        raw_path = settings.get("path")
        if not raw_path:
            continue

        path = Path(os.path.expandvars(raw_path)).expanduser()
        projects[name] = path

    return projects


def choose_project(
    projects: dict[str, Path],
    search_term: str | None,
) -> tuple[str, Path]:
    if not projects:
        raise RuntimeError("Er zijn geen projecten geconfigureerd.")

    if search_term:
        matches = [
            (name, path)
            for name, path in projects.items()
            if search_term.lower() in name.lower()
        ]

        if len(matches) == 1:
            return matches[0]

        if not matches:
            raise RuntimeError(
                f"Geen project gevonden voor: {search_term}"
            )

        candidates = dict(matches)
    else:
        candidates = projects

    result = subprocess.run(
        [
            "fzf",
            "--prompt=Project: ",
            "--height=60%",
            "--reverse",
        ],
        input="\n".join(candidates.keys()),
        text=True,
        capture_output=True,
        check=False,
    )

    selected_name = result.stdout.strip()

    if not selected_name:
        raise KeyboardInterrupt

    return selected_name, candidates[selected_name]


def tmux_window_exists(name: str) -> bool:
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

    return name in result.stdout.splitlines()


def open_project(name: str, path: Path) -> None:
    if not path.is_dir():
        raise FileNotFoundError(
            f"De projectmap bestaat niet: {path}"
        )

    if not os.environ.get("TMUX"):
        raise RuntimeError(
            "Start 'work' vanuit tmux. WezTerm hoort tmux automatisch te openen."
        )

    safe_window_name = name.replace(":", "-")

    if tmux_window_exists(safe_window_name):
        run(
            [
                "tmux",
                "select-window",
                "-t",
                safe_window_name,
            ]
        )
    else:
        run(
            [
                "tmux",
                "new-window",
                "-n",
                safe_window_name,
                "-c",
                str(path),
            ]
        )

    subprocess.Popen(
        ["cursor", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open een RDE-project in tmux en Cursor."
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="Optionele volledige of gedeeltelijke projectnaam.",
    )
    args = parser.parse_args()

    try:
        projects = load_projects()
        name, path = choose_project(projects, args.project)
        open_project(name, path)

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
