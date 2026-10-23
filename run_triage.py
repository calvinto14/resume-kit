"""
run_triage.py — Convenience wrapper: years math + knockout + fit scoring in one call.

The agent still classifies criteria (has/adjacent/missing); this script runs the
deterministic gates and prints a markdown evidence-card skeleton.

Usage (from the Resumes directory):
  python run_triage.py triage/triage_input.json
  python run_triage.py queue/<slug>/triage_input.json
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent

# Imported after ROOT is set. score_requirements has no side effects beyond argparse.
sys.path.insert(0, str(ROOT))
from score_requirements import glance_verdict  # noqa: E402


def run_subprocess(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    snap_code, snap_out = run_subprocess([sys.executable, str(ROOT / "compile_snapshot.py")])
    if snap_code != 0:
        print("Snapshot compile failed:\n", snap_out)
        return snap_code

    input_path = Path(sys.argv[1])
    payload = json.loads(input_path.read_text(encoding="utf-8"))

    jd = payload.get("jd", {})
    years_required = payload.get("years_required")
    profile_path = payload.get("profile_path", "candidate_profile.json")

    years_result = None
    if years_required is not None:
        code, out = run_subprocess(
            [
                sys.executable,
                str(ROOT / "years_math.py"),
                "--required",
                str(years_required),
                "--profile",
                str(profile_path),
            ]
        )
        if code != 0:
            print("Years math failed:\n", out)
            return code
        years_result = json.loads(out)

    knockout_payload = payload.get("knockout", {})
    if years_result:
        knockout_payload.setdefault("years", {})
        knockout_payload["years"].update(
            {
                "required": years_result["years_required"],
                "have": years_result["years_have"],
                "level": payload.get("years_level", "required"),
            }
        )

    knockout_path = input_path.parent / f"{input_path.stem}_knockout.json"
    knockout_path.write_text(json.dumps(knockout_payload, indent=2), encoding="utf-8")
    ko_code, ko_out = run_subprocess(
        [sys.executable, str(ROOT / "knockout_check.py"), str(knockout_path)]
    )
    knockout_result = json.loads(ko_out)

    scored_path = input_path.parent / f"{input_path.stem}_scored.json"
    scored_payload = {
        "required_floor_ratio": payload.get("required_floor_ratio", 0.7),
        "criteria": payload.get("criteria", []),
    }
    scored_path.write_text(json.dumps(scored_payload, indent=2), encoding="utf-8")
    score_code, score_out = run_subprocess(
        [sys.executable, str(ROOT / "score_requirements.py"), str(scored_path)]
    )
    if score_code not in (0,):
        print("Score requirements failed:\n", score_out)
        return score_code
    score_result = json.loads(score_out)

    req = score_result["required_buckets"]
    pref = score_result["preferred_buckets"]
    floor = float(payload.get("required_floor_ratio", 0.7))
    ratio = float(score_result.get("effective_ratio") or 0)
    verdict = glance_verdict(
        bool(knockout_result["passed"]),
        ratio,
        int(req["total"]),
        floor,
    )
    archetype = payload.get("archetype_hint") or "01-SWE"
    company = jd.get("company") or "Unknown"
    title = jd.get("title") or "Unknown"
    if knockout_result["passed"]:
        year_bit = "years ok" if years_result is None else (
            f"years {years_result['years_have']} vs {years_result['years_required']}"
        )
    else:
        year_bit = "; ".join(knockout_result.get("failures") or ["knockout"])
    line = (
        f"{verdict}  {archetype}  "
        f"{req['has']} has / {req['adjacent']} adjacent / {req['missing']} missing  "
        f"{year_bit}"
    )
    print(f"## {company} — {title}")
    print(line)
    print("Reply `baseline <slug>` or `tailor <slug>` for a keeper. Clear a FAIL.")

    detail = [
        f"# Gate detail — {company} — {title}",
        "",
        line,
        "",
        f"Suggested action (legacy): {score_result['suggested_action']} — {score_result['suggested_rationale']}",
        f"Effective required ratio: {ratio:.0%}",
        f"Preferred: {pref['has']} has / {pref['adjacent']} adjacent / {pref['missing']} missing",
        f"Blocking: {', '.join(score_result['blocking_gaps']) or 'none'}",
        f"Coachable: {', '.join(score_result['coachable_gaps']) or 'none'}",
        f"Borderline: {'yes' if score_result.get('escalate_judgment') else 'no'}",
    ]
    if score_result.get("escalate_reasons"):
        detail.append("Borderline reasons: " + "; ".join(score_result["escalate_reasons"]))
    lexicon = payload.get("lexicon_map") or []
    for row in lexicon:
        token = row.get("jd_token", "?")
        status = row.get("status", "?")
        echo = row.get("echo_in") or "do not echo"
        detail.append(f"Lexicon: {token} {status} → {echo}")
    gate_path = input_path.parent / f"{input_path.stem}_gate.md"
    gate_path.write_text("\n".join(detail) + "\n", encoding="utf-8")
    print(f"Detail: `{gate_path}`")

    # Pin into an isolated queue slot so other JDs can be ingested without clobbering this one.
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    pin_cmd = [
        sys.executable,
        str(ROOT / "jd_queue.py"),
        "ingest-and-pin",
        "--triage-input",
        str(input_path),
    ]
    try:
        input_path.resolve().relative_to((ROOT / "queue").resolve())
    except ValueError:
        pin_cmd.append("--paste")

    pin_code, pin_out = run_subprocess(pin_cmd)
    if pin_code == 0:
        try:
            pin_result = json.loads(pin_out)
            print(f"Slug: `{pin_result.get('slug', 'unknown')}`")
        except json.JSONDecodeError:
            print("\n### JD queue pin\n", pin_out)
    else:
        print("\n### JD queue pin failed\n", pin_out)

    if not knockout_result["passed"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
