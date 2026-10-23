"""Build snapshot.json, the hot-path read set for classify and tailor.

One file. Overwritten when a source hash changes. It does not grow with
the number of roles, and nothing deletes it on a timer. Delete it by hand
and the next run rebuilds it.

Usage:
  python compile_snapshot.py
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from kit_paths import experience_rel, load_profile, resume_rel, source_paths

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "snapshot.json"

ARCHETYPES = ("01-SWE", "02-SWE-Adjacent", "03-FDE", "04-GTM-Engineer")

ITEM_RE = re.compile(r"\\resumeItem\{(.*?)\}", re.S)
LATEX_CMD_RE = re.compile(r"\\[a-zA-Z]+\{([^{}]*)\}")
LATEX_SIMPLE_RE = re.compile(r"\\[a-zA-Z]+")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain_bullet(raw: str) -> str:
    text = raw.replace("\\%", "%").replace("\\$", "$").replace("\\&", "&")
    text = LATEX_CMD_RE.sub(r"\1", text)
    text = LATEX_SIMPLE_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def bullets_in(tex: str) -> list[str]:
    return [plain_bullet(match.group(1)) for match in ITEM_RE.finditer(tex)]


def lexicon_section(experience: str) -> str:
    start = experience.find("## JD lexicon echo")
    if start < 0:
        return ""
    end = experience.find("\n## 1.", start)
    return experience[start:end].strip()


def current_hashes(paths: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for rel in paths:
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"Missing snapshot source: {rel}")
        hashes[rel] = sha256(path)
    return hashes


def build(hashes: dict[str, str], profile: dict) -> dict:
    experience_path = ROOT / experience_rel(profile)
    resume_path = ROOT / resume_rel(profile)
    experience = experience_path.read_text(encoding="utf-8")
    library = (ROOT / "resumeSource.tex").read_text(encoding="utf-8")
    basename = resume_path.name
    archetypes = {}
    for name in ARCHETYPES:
        folder = ROOT / "BaselineResumes" / name
        tex_rel = f"BaselineResumes/{name}/{basename}"
        archetypes[name] = {
            "tex": tex_rel,
            "notes": (folder / "notes.md").read_text(encoding="utf-8"),
            "bullets": bullets_in((ROOT / tex_rel).read_text(encoding="utf-8")),
        }
    return {
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": hashes,
        "profile": profile,
        "lexicon": lexicon_section(experience),
        "library_bullets": bullets_in(library),
        "root_bullets": bullets_in(resume_path.read_text(encoding="utf-8")),
        "archetypes": archetypes,
        "read_rule": (
            "Classify and tailor from this file plus the job description. "
            "Patterns/tailoring-lessons.md is an archive. Open the experience file "
            "only to confirm a citation that is not already in lexicon or bullets."
        ),
    }


def main() -> int:
    profile = load_profile(ROOT)
    hashes = current_hashes(source_paths(profile))
    if OUT.is_file():
        try:
            existing = json.loads(OUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        if existing.get("sources") == hashes:
            print(json.dumps({"rebuilt": False, "path": "snapshot.json"}))
            return 0
    payload = build(hashes, profile)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rebuilt": True, "path": "snapshot.json"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
