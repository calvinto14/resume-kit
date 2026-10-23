"""
score_requirements.py — Categorical fit buckets for resume triage.

Takes agent-classified required/preferred criteria (has | adjacent | missing)
and produces bucket counts plus a skip | baseline | tailor recommendation.
Also flags borderline cases that should be re-judged by Opus 5 before the human decides.
No decimal grade — categorical only.

Usage (from the Resumes directory):
  python score_requirements.py triage/scored_criteria.json

Input JSON schema:
{
  "required_floor_ratio": 0.7,
  "criteria": [
    {
      "requirement": "Python",
      "level": "required",
      "status": "has",
      "evidence": "Languages line; SAS bullets"
    },
    {
      "requirement": "Apache Spark",
      "level": "required",
      "status": "missing",
      "evidence": "No Spark in approved sources"
    }
  ]
}
"""

from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

# Guarded: run_triage.py imports this module after wrapping stdout itself.
# A second TextIOWrapper on the same buffer closes it when the first wrapper is collected.
if getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VALID_STATUSES = {"has", "adjacent", "missing"}
VALID_LEVELS = {"required", "preferred"}


def bucket_criteria(criteria: list[dict]) -> dict:
    required = [c for c in criteria if c.get("level", "required") == "required"]
    preferred = [c for c in criteria if c.get("level") == "preferred"]

    def summarize(items: list[dict]) -> dict:
        counts = Counter(c.get("status", "missing") for c in items)
        return {
            "has": counts.get("has", 0),
            "adjacent": counts.get("adjacent", 0),
            "missing": counts.get("missing", 0),
            "total": len(items),
        }

    blocking = [c for c in required if c.get("status") == "missing"]
    coachable = [
        c
        for c in required
        if c.get("status") == "adjacent"
    ]
    ignorable = [c for c in preferred if c.get("status") in {"missing", "adjacent"}]

    return {
        "required_buckets": summarize(required),
        "preferred_buckets": summarize(preferred),
        "blocking_gaps": [c["requirement"] for c in blocking],
        "coachable_gaps": [c["requirement"] for c in coachable],
        "ignorable_gaps": [c["requirement"] for c in ignorable],
    }


def recommend(required_buckets: dict, floor_ratio: float) -> tuple[str, str, float]:
    total = required_buckets["total"]
    if total == 0:
        return (
            "baseline",
            "No required criteria supplied; default to baseline resume.",
            0.0,
        )

    has = required_buckets["has"]
    adjacent = required_buckets["adjacent"]
    effective = has + (0.5 * adjacent)
    ratio = effective / total

    if ratio >= 0.85:
        return (
            "tailor",
            "Strong required-criteria match; tailoring is likely worth the effort.",
            ratio,
        )
    if ratio >= floor_ratio:
        return (
            "tailor",
            f"Required fit at or above floor ({floor_ratio:.0%}); tailor if the role is a priority.",
            ratio,
        )
    if ratio >= floor_ratio - 0.15:
        return (
            "baseline",
            "Partial required fit; baseline resume may be enough unless the company is high priority.",
            ratio,
        )
    return (
        "skip",
        "Low required-criteria match; tailoring is unlikely to move the needle.",
        ratio,
    )


def glance_verdict(
    knockout_passed: bool,
    ratio: float,
    required_total: int,
    floor_ratio: float,
) -> str:
    """One-word review: FAIL, BASELINE, or PASS.

    PASS is a strong required match (85%+). The old 70–85% tailor band is
    BASELINE unless the user promotes that slug. Knockouts are FAIL.
    """
    if not knockout_passed:
        return "FAIL"
    if required_total == 0:
        return "BASELINE"
    if ratio >= 0.85:
        return "PASS"
    if ratio >= floor_ratio - 0.15:
        return "BASELINE"
    return "FAIL"


def escalate_judgment(
    action: str,
    ratio: float,
    floor_ratio: float,
    required_buckets: dict,
    coachable_gaps: list[str],
) -> tuple[bool, list[str]]:
    """Flag cases where Opus 5 should re-judge has/adjacent/missing before the human decides."""
    reasons: list[str] = []
    adjacent = required_buckets["adjacent"]
    missing = required_buckets["missing"]
    total = required_buckets["total"]

    # Soft band between skip and tailor (script suggests baseline)
    if action == "baseline":
        reasons.append("partial required fit (baseline band)")

    # Near a decision threshold (±5 percentage points)
    for threshold, name in (
        (0.85, "strong-tailor"),
        (floor_ratio, "floor"),
        (floor_ratio - 0.15, "skip-floor"),
    ):
        if total > 0 and abs(ratio - threshold) <= 0.05:
            reasons.append(f"ratio {ratio:.0%} near {name} threshold ({threshold:.0%})")

    if adjacent >= 2:
        reasons.append(f"{adjacent} required criteria marked adjacent")

    if missing >= 1 and action == "tailor":
        reasons.append("tailor suggested despite blocking (missing) required criteria")

    if len(coachable_gaps) >= 2 and action in {"tailor", "baseline"}:
        reasons.append("multiple coachable required gaps")

    # Dedupe while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            ordered.append(reason)

    return bool(ordered), ordered


def run(payload: dict) -> dict:
    criteria = payload.get("criteria") or []
    for item in criteria:
        if item.get("status") not in VALID_STATUSES:
            raise ValueError(f"Invalid status for {item.get('requirement')}: {item.get('status')}")
        if item.get("level", "required") not in VALID_LEVELS:
            raise ValueError(f"Invalid level for {item.get('requirement')}: {item.get('level')}")

    floor = float(payload.get("required_floor_ratio", 0.7))
    buckets = bucket_criteria(criteria)
    action, rationale, ratio = recommend(buckets["required_buckets"], floor)
    borderline, escalate_reasons = escalate_judgment(
        action,
        ratio,
        floor,
        buckets["required_buckets"],
        buckets["coachable_gaps"],
    )

    return {
        "required_buckets": buckets["required_buckets"],
        "preferred_buckets": buckets["preferred_buckets"],
        "blocking_gaps": buckets["blocking_gaps"],
        "coachable_gaps": buckets["coachable_gaps"],
        "ignorable_gaps": buckets["ignorable_gaps"],
        "suggested_action": action,
        "suggested_rationale": rationale,
        "effective_ratio": round(ratio, 3),
        "borderline": borderline,
        "escalate_judgment": borderline,
        "escalate_reasons": escalate_reasons,
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
    try:
        result = run(payload)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
