"""
knockout_check.py — Hard dealbreaker gate for resume triage.

Evaluates structured knockout checks supplied by the agent after JD extraction.
Pure rule evaluation; no LLM. Location / relocation / onsite / hybrid / timezone
items in other_knockouts are ignored (`candidate_profile.json` ignore_location).

Usage (from the Resumes directory):
  python knockout_check.py triage/knockout_input.json

Input JSON schema:
{
  "years": {"required": 6, "have": 4.0, "level": "required"},
  "work_authorization_ok": true,
  "certifications_required": ["Databricks Certification"],
  "certifications_held": [],
  "other_knockouts": [
    {"label": "Must hold active TS/SCI clearance", "met": false, "level": "required"}
  ]
}
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# candidate_profile.json ignore_location — never fail the gate on city/hybrid/relocation.
_LOCATION_KNOCKOUT = re.compile(
    r"relocati|onsite|on-site|in-office|\bin office\b|\bhybrid\b|\bcommute\b|"
    r"timezone|time.?zone|\blocation\b|no relocation",
    re.IGNORECASE,
)


def _is_location_item(label: str) -> bool:
    return bool(_LOCATION_KNOCKOUT.search(label or ""))


def evaluate(payload: dict) -> dict:
    failures: list[str] = []
    warnings: list[str] = []

    years = payload.get("years")
    if years and years.get("level") == "required":
        required = float(years.get("required", 0))
        have = float(years.get("have", 0))
        if have < required:
            failures.append(
                f"Years: JD requires {required:g}+ years; profile shows {have:g} relevant years."
            )

    if payload.get("work_authorization_ok") is False:
        failures.append("Work authorization: JD requires eligibility not met in profile.")

    required_certs = payload.get("certifications_required") or []
    held = set(payload.get("certifications_held") or [])
    for cert in required_certs:
        if cert not in held:
            failures.append(f"Certification: required '{cert}' not held.")

    for item in payload.get("other_knockouts") or []:
        label = item.get("label", "Unnamed requirement")
        if _is_location_item(label):
            continue
        level = item.get("level", "required")
        met = item.get("met", True)
        if level == "required" and not met:
            failures.append(f"Knockout: {label}")
        elif level == "preferred" and not met:
            warnings.append(f"Preferred gap: {label}")

    passed = len(failures) == 0
    return {
        "passed": passed,
        "failures": failures,
        "warnings": warnings,
        "recommendation": "skip" if not passed else "continue_triage",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(json.dumps({"error": f"File not found: {path}"}, indent=2))
        return 1

    payload = json.loads(path.read_text(encoding="utf-8"))
    result = evaluate(payload)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
