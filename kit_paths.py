"""Paths for the live candidate. Scripts read candidate_profile.json, not a hardcoded name."""

from __future__ import annotations

import json
from pathlib import Path

ARCHETYPES = ("01-SWE", "02-SWE-Adjacent", "03-FDE", "04-GTM-Engineer")


def load_profile(root: Path | None = None) -> dict:
    root = root or Path(__file__).resolve().parent
    path = root / "candidate_profile.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resume_basename(profile: dict) -> str:
    name = str(profile.get("resume_basename") or "Resume").strip()
    if name.lower().endswith(".tex"):
        name = name[:-4]
    return name or "Resume"


def resume_rel(profile: dict) -> str:
    return f"{resume_basename(profile)}.tex"


def experience_rel(profile: dict) -> str:
    return str(profile.get("experience_file") or "experience.md")


def source_paths(profile: dict) -> list[str]:
    base = resume_rel(profile)
    paths = [
        experience_rel(profile),
        "resumeSource.tex",
        "Patterns/tailoring-lessons.md",
        "candidate_profile.json",
        base,
    ]
    for name in ARCHETYPES:
        paths.append(f"BaselineResumes/{name}/{base}")
        paths.append(f"BaselineResumes/{name}/notes.md")
    return paths
