"""

log_override.py — Append a human vs script decision override to triage/decision_overrides.md.



Usage (from the Resumes directory):

  python log_override.py --suggested skip --chosen tailor --why "Priority company"

  python log_override.py --suggested baseline --chosen skip --why "Too many missing required" \\

      --label "Acme · SWE II" --borderline yes --fit "has 3 / adj 2 / miss 2"

"""



from __future__ import annotations



import argparse

import io

import json

import sys

from datetime import date

from pathlib import Path



sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")



ROOT = Path(__file__).resolve().parent

LOG_PATH = ROOT / "triage" / "decision_overrides.md"

PIN_PATH = ROOT / "triage" / "jd_pin.json"

QUEUE = ROOT / "queue"

VALID = {"skip", "baseline", "tailor"}

IN_FLIGHT = {"ingested", "awaiting_decision", "tailoring"}





def label_from_pin(pin: dict) -> str:

    if pin.get("label"):

        return str(pin["label"])

    company = pin.get("company") or "Unknown"

    title = pin.get("title") or "Unknown"

    return f"{company} · {title}"



def slot_label(slug: str) -> str:

    path = QUEUE / slug / "pin.json"

    if not path.is_file():

        return slug

    try:

        return label_from_pin(json.loads(path.read_text(encoding="utf-8")))

    except json.JSONDecodeError:

        return slug



def pin_label() -> str:

    if QUEUE.is_dir():

        inflight = []

        for path in sorted(QUEUE.iterdir()):

            pin_file = path / "pin.json"

            if not path.is_dir() or not pin_file.is_file():

                continue

            try:

                pin = json.loads(pin_file.read_text(encoding="utf-8"))

            except json.JSONDecodeError:

                continue

            if pin.get("status") in IN_FLIGHT:

                inflight.append(label_from_pin(pin))

        if len(inflight) == 1:

            return inflight[0]

        if len(inflight) > 1:

            return "multiple queue slots (pass --slot)"

    if not PIN_PATH.exists():

        return "unknown role"

    try:

        pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))

    except json.JSONDecodeError:

        return "unknown role"

    return label_from_pin(pin)





def append_row(

    suggested: str,

    chosen: str,

    why: str,

    label: str,

    borderline: str,

    fit: str,

) -> None:

    if not LOG_PATH.exists():

        raise FileNotFoundError(f"Missing {LOG_PATH}")



    # Escape pipes so markdown tables stay intact

    def cell(value: str) -> str:

        return value.replace("|", "/").replace("\n", " ").strip()



    row = (

        f"| {date.today().isoformat()} | {cell(label)} | {cell(suggested)} | "

        f"{cell(chosen)} | {cell(why)} | {cell(borderline)} | {cell(fit)} |"

    )

    text = LOG_PATH.read_text(encoding="utf-8")

    if not text.endswith("\n"):

        text += "\n"

    LOG_PATH.write_text(text + row + "\n", encoding="utf-8")

    print(json.dumps({"logged": True, "path": str(LOG_PATH), "row": row}, indent=2))





def main() -> int:

    parser = argparse.ArgumentParser(description="Log a triage decision override")

    parser.add_argument("--suggested", required=True, choices=sorted(VALID))

    parser.add_argument("--chosen", required=True, choices=sorted(VALID))

    parser.add_argument("--why", required=True)

    parser.add_argument("--label", default="")

    parser.add_argument("--borderline", default="no", choices=["yes", "no"])

    parser.add_argument("--fit", default="n/a", help='e.g. "has 4 / adj 2 / miss 1"')

    parser.add_argument("--slot", default="", help="queue slug (required when multiple roles are in flight)")

    args = parser.parse_args()



    if args.suggested == args.chosen:

        print(

            json.dumps(

                {

                    "logged": False,

                    "reason": "suggested equals chosen; nothing to override",

                },

                indent=2,

            )

        )

        return 0



    label = args.label.strip() or (slot_label(args.slot.strip()) if args.slot.strip() else pin_label())

    append_row(

        suggested=args.suggested,

        chosen=args.chosen,

        why=args.why,

        label=label,

        borderline=args.borderline,

        fit=args.fit,

    )

    return 0





if __name__ == "__main__":

    raise SystemExit(main())


