#!/usr/bin/env python3
"""Tell the agent to run /tailor when inbox/*.md (not README) appears or is edited."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "inbox"


def inbox_jds() -> list[str]:
    if not INBOX.is_dir():
        return []
    names = []
    for path in sorted(INBOX.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        if path.stem.lower() == "readme":
            continue
        names.append(path.name)
    return names


def is_inbox_jd(file_path: str) -> bool:
    if not file_path:
        return False
    normalized = file_path.replace("\\", "/")
    name = Path(normalized).name
    if name.lower() == "readme.md":
        return False
    return "/inbox/" in f"/{normalized}" and name.lower().endswith(".md")


def message_for(files: list[str]) -> str:
    listed = ", ".join(files)
    return (
        "Inbox has new JD file(s): "
        f"{listed}. Run the tailor skill Phase 0 now: "
        "`python3 jd_queue.py ingest --move` (inbox only; do not ingest JobDescription.md "
        "unless the user asked). Classify new slots from snapshot.json, pin, show one PASS/BASELINE/FAIL line per slug. "
        "If the user already said tailor, proceed to Phase 1 after gates. "
        "Do not re-open cleared queue slots or copy finished JDs back into inbox/."
    )


def main() -> int:
    raw = sys.stdin.read()
    payload = {}
    if raw.strip():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}

    files = inbox_jds()
    file_path = (
        payload.get("file_path")
        or payload.get("path")
        or payload.get("filePath")
        or ""
    )
    if isinstance(file_path, str) and is_inbox_jd(file_path):
        name = Path(file_path).name
        if name not in files:
            files = [name] + files

    if not files:
        print("{}")
        return 0

    out = {
        "additional_context": message_for(files),
        "user_message": f"New inbox JD ready: {', '.join(files)}",
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
