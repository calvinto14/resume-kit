"""Check that this kit can tailor a resume for the person who owns it.

Usage (from the repo root):
  python doctor.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from kit_paths import ARCHETYPES, experience_rel, load_profile, resume_rel

ROOT = Path(__file__).resolve().parent


def check(ok: bool, label: str) -> bool:
    mark = "ok" if ok else "MISSING"
    print(f"  [{mark}] {label}")
    return ok


def main() -> int:
    print("Resume kit doctor")
    ready = True

    ready &= check(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]} (need 3.9+)")
    ready &= check(shutil.which("pdflatex") is not None, "pdflatex on PATH (MacTeX or TeX Live)")

    profile_path = ROOT / "candidate_profile.json"
    profile: dict = {}
    if profile_path.is_file():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            ready &= check(True, "candidate_profile.json parses")
        except json.JSONDecodeError as exc:
            ready &= check(False, f"candidate_profile.json parses ({exc})")
    else:
        ready &= check(False, "candidate_profile.json exists")

    experience = ROOT / experience_rel(profile)
    ready &= check(experience.is_file(), f"{experience_rel(profile)} exists")
    if experience.is_file():
        text = experience.read_text(encoding="utf-8")
        populated = "Status: not set up" not in text and "## 1. Placeholder" not in text
        ready &= check(populated, "experience.md has real stories (run /setup)")
        ready &= check("## JD lexicon echo" in text, "experience.md has a JD lexicon echo section")

    resume = ROOT / resume_rel(profile)
    ready &= check(resume.is_file(), f"{resume_rel(profile)} exists")
    for name in ARCHETYPES:
        folder = ROOT / "BaselineResumes" / name
        ready &= check((folder / resume.name).is_file(), f"BaselineResumes/{name}/{resume.name}")
        ready &= check((folder / "notes.md").is_file(), f"BaselineResumes/{name}/notes.md")

    setup_done = bool(profile.get("setup_complete"))
    ready &= check(setup_done, "candidate_profile.json setup_complete is true")
    if setup_done:
        employment = profile.get("employment") or []
        ready &= check(bool(employment), "at least one employment entry")
        ready &= check(bool(profile.get("full_name")), "full_name is set")
        ready &= check(profile.get("work_authorization_ok") is True or profile.get("work_authorization_ok") is False, "work_authorization_ok is true or false")

    print()
    if ready:
        print("Ready. Paste a job description and say /tailor.")
        return 0
    print("Not ready. Open this folder in Cursor and say /setup.")
    print("Install a TeX distribution first if pdflatex is missing.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
