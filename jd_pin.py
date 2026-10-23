"""
jd_pin.py — Compatibility wrapper around jd_queue.py.

Pins still exist so older skill text (`python jd_pin.py verify`) keeps working.
New work should call `jd_queue.py` with a slug when more than one role is in flight.

Usage (from repo root):
  python jd_pin.py pin [path] [slug]       # default path: JobDescription.md
  python jd_pin.py verify [slug]           # required if multiple queue slots
  python jd_pin.py clear [slug]
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "JobDescription.md"
QUEUE = ROOT / "queue"
LEGACY_TRIAGE_INPUT = ROOT / "triage" / "triage_input.json"


def run_queue(args: list[str]) -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "jd_queue.py"), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if out:
        print(out)
    if err and proc.returncode != 0:
        print(err)
    return proc.returncode


def slug_from_path(path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(QUEUE.resolve())
    except ValueError:
        return None
    return rel.parts[0] if rel.parts else None


def cmd_pin(source: Path, slug: str | None) -> int:
    if slug:
        return run_queue(["pin", slug])
    inferred = slug_from_path(source)
    if inferred:
        return run_queue(["pin", inferred])
    args = ["ingest-and-pin", "--source", str(source)]
    if source.resolve() == DEFAULT_SOURCE.resolve():
        args.append("--paste")
    if LEGACY_TRIAGE_INPUT.is_file():
        args.extend(["--triage-input", str(LEGACY_TRIAGE_INPUT)])
    return run_queue(args)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1].lower()
    rest = sys.argv[2:]

    if command == "pin":
        source = DEFAULT_SOURCE
        slug = None
        if rest:
            maybe_path = Path(rest[0])
            if not maybe_path.is_absolute():
                maybe_path = ROOT / maybe_path
            if maybe_path.exists() or maybe_path.suffix.lower() in {".md", ".txt"}:
                source = maybe_path
                slug = rest[1] if len(rest) > 1 else None
            else:
                slug = rest[0]
        return cmd_pin(source, slug)
    if command == "verify":
        args = ["verify"]
        if rest:
            args.append(rest[0])
        return run_queue(args)
    if command == "clear":
        args = ["clear"]
        if rest:
            args.append(rest[0])
        return run_queue(args)

    print(f"Unknown command: {command}\n{__doc__}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
