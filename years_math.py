"""
years_math.py — Deterministic years-of-experience math for resume triage.

Computes total relevant employment years from candidate_profile.json and
compares to a JD minimum. The agent extracts years_required from the JD; this
script does the date math so the number is consistent every run.

Usage (from the Resumes directory):
  python years_math.py --required 6
  python years_math.py --required 6 --profile candidate_profile.json
  python years_math.py --json '{"years_required": 6}'
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DEFAULT_PROFILE = Path("candidate_profile.json")


def parse_month(value: str) -> date:
    year_str, month_str = value.split("-", 1)
    return date(int(year_str), int(month_str), 1)


def months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def compute_relevant_years(profile: dict, as_of: date | None = None) -> float:
    as_of = as_of or date.today()
    total_months = 0
    for job in profile.get("employment", []):
        if not job.get("relevant", True):
            continue
        start = parse_month(job["start"])
        end_str = job.get("end")
        end = parse_month(end_str) if end_str else as_of
        total_months += max(0, months_between(start, end))
    return round(total_months / 12.0, 1)


def run(years_required: float, profile_path: Path, as_of: date | None = None) -> dict:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    years_have = compute_relevant_years(profile, as_of=as_of)
    years_gap = round(max(0.0, years_required - years_have), 1)
    meets_minimum = years_have >= years_required
    return {
        "years_required": years_required,
        "years_have": years_have,
        "years_gap": years_gap,
        "meets_minimum": meets_minimum,
        "profile_path": str(profile_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare JD years requirement to profile.")
    parser.add_argument("--required", type=float, help="Minimum years required by the JD")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--json", type=str, help='Inline JSON, e.g. {"years_required": 6}')
    parser.add_argument(
        "--as-of",
        type=str,
        help="Override today's date for testing (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    if args.json:
        payload = json.loads(args.json)
        years_required = float(payload["years_required"])
    elif args.required is not None:
        years_required = args.required
    else:
        parser.error("Provide --required N or --json '{\"years_required\": N}'")

    as_of = date.fromisoformat(args.as_of) if args.as_of else None

    if not args.profile.exists():
        print(json.dumps({"error": f"Profile not found: {args.profile}"}, indent=2))
        return 1

    result = run(years_required, args.profile, as_of=as_of)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
