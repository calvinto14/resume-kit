"""
jd_queue.py — Isolated per-role JD slots so /tailor can triage up to 5 roles at once
without overwriting a single pin.

Usage (from repo root):
  python jd_queue.py ingest [--paste] [--move] [paths...]
  python jd_queue.py list [--json]
  python jd_queue.py relabel [slug]
  python jd_queue.py pin <slug>
  python jd_queue.py verify [slug]
  python jd_queue.py decide <slug> skip|baseline|tailor
  python jd_queue.py clear [slug]
  python jd_queue.py ingest-and-pin [--paste] [--triage-input PATH] [--source PATH]
  python jd_queue.py migrate-legacy
  python jd_queue.py rename <old> <new>
  python jd_queue.py paths <slug>
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("RESUME_ROOT", Path(__file__).resolve().parent))
INBOX = ROOT / "inbox"
QUEUE = ROOT / "queue"
PASTE = ROOT / "JobDescription.md"
TRIAGE_DIR = ROOT / "triage"
LEGACY_PIN = TRIAGE_DIR / "jd_pin.json"
LEGACY_SNAPSHOT = TRIAGE_DIR / "jd_snapshot.md"
LEGACY_TRIAGE_INPUT = TRIAGE_DIR / "triage_input.json"

MAX_IN_FLIGHT = 5
RECOMMENDED_BATCH = 3
MAX_PHASE1_PARALLEL = 2
MIN_PASTE_CHARS = 80
IN_FLIGHT = frozenset({"ingested", "awaiting_decision", "tailoring"})
DECISIONS = frozenset({"skip", "baseline", "tailor"})


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").splitlines()).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def dump(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return code


def slugify(*parts: str) -> str:
    text = "-".join(p.strip() for p in parts if p and str(p).strip())
    text = re.sub(r"[^A-Za-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:80] or "untitled"


def short_role_slug(company: str, title: str) -> str:
    title = re.sub(r"\([^)]*\)", " ", title)
    title = re.sub(r"\bALL LEVELS\b", " ", title, flags=re.I)
    return slugify(company, title)[:60]


def slot_dir(slug: str) -> Path:
    return QUEUE / slug


def pin_path(slug: str) -> Path:
    return slot_dir(slug) / "pin.json"


def jd_path(slug: str) -> Path:
    return slot_dir(slug) / "jd.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_pin(slug: str) -> dict | None:
    path = pin_path(slug)
    if not path.is_file():
        return None
    return load_json(path)


def save_pin(slug: str, pin: dict) -> None:
    pin["slug"] = slug
    pin["jd_path"] = rel(jd_path(slug))
    pin["triage_input_path"] = rel(slot_dir(slug) / "triage_input.json")
    write_json(pin_path(slug), pin)


def label_of(pin: dict) -> str:
    company = pin.get("company") or "Unknown"
    title = pin.get("title") or "Unknown"
    return f"{company} · {title}"


def iter_slugs() -> list[str]:
    if not QUEUE.is_dir():
        return []
    slugs = []
    for path in sorted(QUEUE.iterdir()):
        if path.is_dir() and (path / "pin.json").is_file():
            slugs.append(path.name)
    return slugs


def in_flight_slugs() -> list[str]:
    out = []
    for slug in iter_slugs():
        pin = load_pin(slug) or {}
        if pin.get("status") in IN_FLIGHT:
            out.append(slug)
    return out


def find_slug_by_hash(sha: str) -> str | None:
    for slug in iter_slugs():
        pin = load_pin(slug) or {}
        if pin.get("content_sha256") == sha:
            return slug
    return None


def slug_from_input_path(path: Path) -> str | None:
    resolved = path if path.is_absolute() else ROOT / path
    try:
        rel_path = resolved.resolve().relative_to((ROOT / "queue").resolve())
    except ValueError:
        return None
    parts = rel_path.parts
    return parts[0] if parts else None


def available_slug(base: str, current: str | None = None) -> str:
    slug = base
    n = 2
    while slot_dir(slug).exists() and slug != current:
        slug = f"{base}-{n}"
        n += 1
    return slug


def unique_slug(base: str, sha: str) -> str:
    existing = find_slug_by_hash(sha)
    if existing:
        return existing
    return available_slug(base)


def meta_from_triage_input(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    try:
        return load_json(path).get("jd") or {}
    except json.JSONDecodeError:
        return {}


def paste_is_usable() -> bool:
    if not PASTE.is_file():
        return False
    return len(normalize(PASTE.read_text(encoding="utf-8"))) >= MIN_PASTE_CHARS


def inbox_files() -> list[Path]:
    if not INBOX.is_dir():
        return []
    files = []
    for path in sorted(INBOX.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() != ".md":
            continue
        if path.stem.lower() == "readme":
            continue
        files.append(path)
    return files


def copy_sidecars(src_dir: Path, dest_dir: Path, stem: str = "triage_input") -> list[str]:
    copied = []
    mapping = {
        f"{stem}.json": "triage_input.json",
        f"{stem}_knockout.json": "triage_input_knockout.json",
        f"{stem}_scored.json": "triage_input_scored.json",
    }
    for src_name, dest_name in mapping.items():
        src = src_dir / src_name
        dest_file = dest_dir / dest_name
        if not src.is_file():
            continue
        if src.resolve() == dest_file.resolve():
            continue
        shutil.copy2(src, dest_file)
        copied.append(dest_name)
    return copied


def refresh_meta(pin: dict, slug: str) -> dict:
    meta = meta_from_triage_input(slot_dir(slug) / "triage_input.json")
    if meta:
        pin["title"] = meta.get("title") or pin.get("title")
        pin["company"] = meta.get("company") or pin.get("company")
        pin["link"] = meta.get("link") or pin.get("link") or ""
    return pin


def make_slot(slug: str, content: str, source_path: str, status: str = "ingested") -> dict:
    dest = slot_dir(slug)
    dest.mkdir(parents=True, exist_ok=True)
    jd_path(slug).write_text(content, encoding="utf-8")
    pin = {
        "slug": slug,
        "source_path": source_path,
        "title": None,
        "company": None,
        "link": "",
        "content_sha256": content_hash(content),
        "created_at": now_iso(),
        "pinned_at": None,
        "status": status,
        "jd_path": rel(jd_path(slug)),
        "triage_input_path": rel(dest / "triage_input.json"),
    }
    save_pin(slug, pin)
    return pin


def ingest_one(source: Path, move: bool) -> dict:
    if not source.is_file():
        return {"ok": False, "error": f"Source not found: {source}"}
    content = source.read_text(encoding="utf-8")
    if len(normalize(content)) < MIN_PASTE_CHARS:
        return {"ok": False, "error": f"Source too short to ingest: {rel(source)}"}
    sha = content_hash(content)
    existing = find_slug_by_hash(sha)
    if existing:
        return {
            "ok": True,
            "slug": existing,
            "deduped": True,
            "status": (load_pin(existing) or {}).get("status"),
            "source_path": rel(source),
        }

    in_flight = in_flight_slugs()
    if len(in_flight) >= MAX_IN_FLIGHT:
        return {
            "ok": False,
            "error": f"Queue full ({MAX_IN_FLIGHT} in flight). Decide or clear a slot first.",
            "in_flight": in_flight,
            "source_path": rel(source),
        }

    if source.resolve() == PASTE.resolve():
        base = "paste-" + sha[:8]
    else:
        base = slugify(source.stem)

    slug = unique_slug(base, sha)
    pin = make_slot(slug, content, rel(source), status="ingested")
    result = {
        "ok": True,
        "slug": slug,
        "deduped": False,
        "status": pin["status"],
        "source_path": rel(source),
        "jd_path": pin["jd_path"],
    }
    if move and source.resolve() != PASTE.resolve():
        source.unlink()
        result["moved"] = True
    return result


def slot_summary(slug: str) -> dict:
    pin = load_pin(slug) or {}
    triage = slot_dir(slug) / "triage_input.json"
    return {
        "slug": slug,
        "status": pin.get("status"),
        "label": label_of(pin),
        "company": pin.get("company"),
        "title": pin.get("title"),
        "jd_path": pin.get("jd_path") or rel(jd_path(slug)),
        "triage_input_path": rel(triage),
        "has_triage_input": triage.is_file(),
        "needs_classify": not triage.is_file(),
        "content_sha256": pin.get("content_sha256"),
    }


def ingest_sources(paths: list[Path] | None, paste: bool, move: bool) -> tuple[dict, int]:
    INBOX.mkdir(exist_ok=True)
    QUEUE.mkdir(exist_ok=True)
    sources: list[Path] = []
    if paths is None:
        sources.extend(inbox_files())
    else:
        sources.extend(paths)
    if paste and paste_is_usable():
        paste_already = any(p.resolve() == PASTE.resolve() for p in sources)
        if not paste_already:
            sources.append(PASTE)

    if not sources:
        return (
            {
                "ingested": [],
                "skipped": [],
                "in_flight": len(in_flight_slugs()),
                "max_in_flight": MAX_IN_FLIGHT,
                "recommended_batch": RECOMMENDED_BATCH,
                "message": "Nothing to ingest. Drop JDs in inbox/ or paste into JobDescription.md.",
            },
            0,
        )

    ingested = []
    skipped = []
    for source in sources:
        result = ingest_one(source, move=move)
        if result.get("ok"):
            ingested.append(result)
        else:
            skipped.append(result)
    code = 0 if ingested or not skipped else 1
    return (
        {
            "ingested": ingested,
            "skipped": skipped,
            "in_flight": len(in_flight_slugs()),
            "max_in_flight": MAX_IN_FLIGHT,
            "recommended_batch": RECOMMENDED_BATCH,
            "slots": [slot_summary(s) for s in in_flight_slugs()],
        },
        code,
    )


def cmd_ingest(paths: list[Path] | None, paste: bool, move: bool) -> int:
    payload, code = ingest_sources(paths, paste=paste, move=move)
    return dump(payload, code)


def cmd_list(as_json: bool) -> int:
    slots = [slot_summary(s) for s in iter_slugs()]
    payload = {
        "slots": slots,
        "in_flight": [s for s in slots if s.get("status") in IN_FLIGHT],
        "in_flight_count": len(in_flight_slugs()),
        "max_in_flight": MAX_IN_FLIGHT,
        "recommended_batch": RECOMMENDED_BATCH,
        "max_phase1_parallel": MAX_PHASE1_PARALLEL,
    }
    if as_json or True:
        return dump(payload)
    return dump(payload)


def relabel_slots(slug: str | None) -> tuple[dict, int]:
    targets = [slug] if slug else iter_slugs()
    if not targets:
        return {"error": "No queue slots to relabel"}, 1
    renamed = []
    unchanged = []
    current = slug
    for old in targets:
        pin = load_pin(old)
        if pin is None:
            return {"error": f"Unknown slug: {old}"}, 1
        pin = refresh_meta(pin, old)
        save_pin(old, pin)
        desired = short_role_slug(str(pin.get("company") or ""), str(pin.get("title") or ""))
        if not desired or desired == "untitled" or desired == old:
            unchanged.append({"slug": old, "label": label_of(pin)})
            continue
        new = available_slug(desired, current=old)
        if new == old:
            unchanged.append({"slug": old, "label": label_of(pin)})
            continue
        dest = slot_dir(new)
        if dest.exists() and new != old:
            unchanged.append({"slug": old, "label": label_of(pin), "note": f"target exists: {new}"})
            continue
        slot_dir(old).rename(dest)
        pin["slug"] = new
        save_pin(new, pin)
        renamed.append({"from": old, "to": new, "label": label_of(pin)})
        if current == old:
            current = new
    return {"renamed": renamed, "unchanged": unchanged, "slug": current}, 0


def cmd_relabel(slug: str | None) -> int:
    payload, code = relabel_slots(slug)
    return dump(payload, code)


def pin_slot(slug: str) -> tuple[dict, int]:
    pin = load_pin(slug)
    if pin is None or not jd_path(slug).is_file():
        return {"error": f"Unknown slug or missing jd.md: {slug}"}, 1
    pin = refresh_meta(pin, slug)
    pin["content_sha256"] = content_hash(jd_path(slug).read_text(encoding="utf-8"))
    pin["pinned_at"] = now_iso()
    pin["status"] = "awaiting_decision"
    pin["awaiting_decision"] = True
    save_pin(slug, pin)
    return (
        {
            "pinned": True,
            "slug": slug,
            "label": label_of(pin),
            "snapshot_path": rel(jd_path(slug)),
            "use_for_tailoring": rel(jd_path(slug)),
            "triage_input_path": rel(slot_dir(slug) / "triage_input.json"),
            "in_flight": len(in_flight_slugs()),
            "max_in_flight": MAX_IN_FLIGHT,
            "message": (
                f"JD pinned as queue/{slug}/jd.md. You may paste the next role into "
                "JobDescription.md or drop files in inbox/; this slot stays isolated."
            ),
        },
        0,
    )


def cmd_pin(slug: str) -> int:
    payload, code = pin_slot(slug)
    return dump(payload, code)


def resolve_verify_slug(slug: str | None) -> tuple[str | None, dict | None]:
    if slug:
        return slug, load_pin(slug)
    flight = in_flight_slugs()
    if len(flight) == 1:
        return flight[0], load_pin(flight[0])
    if len(flight) > 1:
        return None, {
            "error": "Multiple queue slots in flight; pass a slug.",
            "slots": [slot_summary(s) for s in flight],
        }
    return None, None


def cmd_verify(slug: str | None) -> int:
    resolved, pin_or_err = resolve_verify_slug(slug)
    if resolved is None and isinstance(pin_or_err, dict) and pin_or_err.get("error"):
        return dump(pin_or_err, 4)
    if resolved is None or pin_or_err is None:
        return dump(
            {
                "has_pin": False,
                "error": "No pending JD pin. Run /tailor (Phase 0) first.",
                "use_for_tailoring": rel(PASTE),
            },
            3,
        )
    pin = pin_or_err
    if not jd_path(resolved).is_file():
        return dump({"has_pin": False, "error": f"Missing {rel(jd_path(resolved))}"}, 3)

    current_exists = PASTE.is_file()
    current_hash = content_hash(PASTE.read_text(encoding="utf-8")) if current_exists else None
    match = current_hash == pin.get("content_sha256") if current_hash else False
    use_path = jd_path(resolved)
    result = {
        "has_pin": True,
        "slug": resolved,
        "awaiting_decision": pin.get("status") in {"ingested", "awaiting_decision", "tailoring"},
        "status": pin.get("status"),
        "pinned_label": label_of(pin),
        "pinned_at": pin.get("pinned_at"),
        "job_description_matches_pin": match,
        "use_for_tailoring": rel(use_path),
        "triage_input_path": rel(slot_dir(resolved) / "triage_input.json"),
        "in_flight": len(in_flight_slugs()),
        "message": (
            f"Tailor against queued JD: {label_of(pin)} ({rel(use_path)})."
            if not match
            else f"JobDescription.md still matches queued JD: {label_of(pin)}."
        ),
    }
    if not match and current_exists:
        result["note"] = (
            "JobDescription.md differs from this slot — expected when the paste buffer "
            "holds another role. Do not re-read JobDescription.md for this tailor."
        )
    code = 0 if pin.get("status") in {"awaiting_decision", "tailoring", "ingested"} else 2
    return dump(result, code)


def cmd_decide(slug: str, decision: str) -> int:
    pin = load_pin(slug)
    if pin is None:
        return dump({"error": f"Unknown slug: {slug}"}, 1)
    decision = decision.lower()
    if decision not in DECISIONS:
        return dump({"error": f"Decision must be skip|baseline|tailor, got {decision}"}, 1)
    if decision == "tailor":
        pin["status"] = "tailoring"
        pin["awaiting_decision"] = False
    elif decision == "skip":
        pin["status"] = "skipped"
        pin["awaiting_decision"] = False
    else:
        pin["status"] = "baseline"
        pin["awaiting_decision"] = False
    pin["decided_at"] = now_iso()
    save_pin(slug, pin)
    return dump(
        {
            "decided": True,
            "slug": slug,
            "decision": decision,
            "status": pin["status"],
            "label": label_of(pin),
            "use_for_tailoring": rel(jd_path(slug)),
        }
    )


def cmd_clear(slug: str | None) -> int:
    if slug is None:
        resolved, pin_or_err = resolve_verify_slug(None)
        if resolved is None and isinstance(pin_or_err, dict) and pin_or_err.get("error"):
            return dump(pin_or_err, 4)
        slug = resolved
    if not slug:
        removed = []
        for path in (LEGACY_PIN, LEGACY_SNAPSHOT):
            if path.exists():
                path.unlink()
                removed.append(rel(path))
        return dump({"cleared": True, "removed": removed, "note": "No queue slot; cleared legacy pin files if present."})

    dest = slot_dir(slug)
    if not dest.exists():
        return dump({"error": f"Unknown slug: {slug}"}, 1)
    shutil.rmtree(dest)
    removed = [rel(dest)]
    for path in (LEGACY_PIN, LEGACY_SNAPSHOT):
        if path.exists():
            path.unlink()
            removed.append(rel(path))
    return dump({"cleared": True, "slug": slug, "removed": removed})


def attach_triage_input(slug: str, triage_input: Path | None) -> None:
    if not triage_input or not triage_input.is_file():
        return
    dest = slot_dir(slug)
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "triage_input.json"
    if triage_input.resolve() != target.resolve():
        shutil.copy2(triage_input, target)
    copy_sidecars(triage_input.parent, dest, stem=triage_input.stem)


def cmd_ingest_and_pin(paste: bool, triage_input: Path | None, source: Path | None) -> int:
    QUEUE.mkdir(exist_ok=True)
    slug_hint = slug_from_input_path(triage_input) if triage_input else None
    if slug_hint:
        attach_triage_input(slug_hint, triage_input)
        renamed, code = relabel_slots(slug_hint)
        if code != 0:
            return dump(renamed, code)
        slug_hint = renamed.get("slug") or slug_hint
        payload, pin_code = pin_slot(slug_hint)
        payload["relabel"] = renamed
        return dump(payload, pin_code)

    ingest_paths = [source] if source else []
    use_paste = False
    if source is None and paste:
        if paste_is_usable():
            ingest_paths = [PASTE]
        use_paste = False
    ingested, ingest_code = ingest_sources(
        ingest_paths, paste=use_paste, move=False
    )
    if ingest_code != 0 and not in_flight_slugs():
        return dump(ingested, ingest_code)

    slug = None
    if source and source.is_file():
        slug = find_slug_by_hash(content_hash(source.read_text(encoding="utf-8")))
    if slug is None and paste and paste_is_usable():
        slug = find_slug_by_hash(content_hash(PASTE.read_text(encoding="utf-8")))
    if slug is None:
        flight = in_flight_slugs()
        if len(flight) == 1:
            slug = flight[0]
    if slug is None:
        ingested["error"] = "ingest-and-pin could not resolve a slot"
        return dump(ingested, 1)

    attach_triage_input(slug, triage_input)
    renamed, relabel_code = relabel_slots(slug)
    if relabel_code != 0:
        return dump(renamed, relabel_code)
    slug = renamed.get("slug") or slug
    payload, pin_code = pin_slot(slug)
    payload["ingest"] = ingested
    payload["relabel"] = renamed
    return dump(payload, pin_code)


def cmd_migrate_legacy() -> int:
    QUEUE.mkdir(exist_ok=True)
    snapshot = None
    if LEGACY_SNAPSHOT.is_file() and len(normalize(LEGACY_SNAPSHOT.read_text(encoding="utf-8"))) >= MIN_PASTE_CHARS:
        snapshot = LEGACY_SNAPSHOT
    elif paste_is_usable():
        snapshot = PASTE
    if snapshot is None:
        return dump({"migrated": False, "reason": "No legacy snapshot or JobDescription.md to migrate"})

    content = snapshot.read_text(encoding="utf-8")
    sha = content_hash(content)
    existing = find_slug_by_hash(sha)
    if existing:
        dest = slot_dir(existing)
        if LEGACY_TRIAGE_INPUT.is_file() and not (dest / "triage_input.json").is_file():
            copy_sidecars(TRIAGE_DIR, dest)
        renamed, relabel_code = relabel_slots(existing)
        if relabel_code != 0:
            return dump(renamed, relabel_code)
        existing = renamed.get("slug") or existing
        pin = load_pin(existing) or {}
        if pin.get("status") == "ingested" and (slot_dir(existing) / "triage_input.json").is_file():
            payload, pin_code = pin_slot(existing)
            payload["migrated"] = True
            payload["deduped"] = True
            payload["relabel"] = renamed
            return dump(payload, pin_code)
        return dump({"migrated": False, "deduped": True, "slug": existing, "status": pin.get("status"), "relabel": renamed})

    meta = meta_from_triage_input(LEGACY_TRIAGE_INPUT)
    base = short_role_slug(str(meta.get("company") or ""), str(meta.get("title") or "")) or ("paste-" + sha[:8])
    slug = unique_slug(base, sha)
    pin = make_slot(slug, content, rel(snapshot), status="ingested")
    copied = []
    if LEGACY_TRIAGE_INPUT.is_file():
        copied = copy_sidecars(TRIAGE_DIR, slot_dir(slug))
        pin = refresh_meta(pin, slug)
        save_pin(slug, pin)
    if (slot_dir(slug) / "triage_input.json").is_file():
        renamed, relabel_code = relabel_slots(slug)
        if relabel_code != 0:
            return dump(renamed, relabel_code)
        slug = renamed.get("slug") or find_slug_by_hash(sha) or slug
        payload, pin_code = pin_slot(slug)
        payload["migrated"] = True
        payload["copied"] = copied
        payload["relabel"] = renamed
        return dump(payload, pin_code)
    return dump({"migrated": True, "slug": slug, "copied": copied, "status": pin.get("status")})


def cmd_rename(old: str, new: str) -> int:
    pin = load_pin(old)
    if pin is None:
        return dump({"error": f"Unknown slug: {old}"}, 1)
    new = slugify(new)
    if not new:
        return dump({"error": "Empty target slug"}, 1)
    if new == old:
        return dump({"renamed": False, "slug": old, "label": label_of(pin)})
    dest = slot_dir(new)
    if dest.exists():
        return dump({"error": f"Target exists: {new}"}, 1)
    slot_dir(old).rename(dest)
    pin["slug"] = new
    save_pin(new, pin)
    return dump({"renamed": True, "from": old, "to": new, "label": label_of(pin)})


def cmd_paths(slug: str) -> int:
    pin = load_pin(slug)
    if pin is None:
        return dump({"error": f"Unknown slug: {slug}"}, 1)
    dest = slot_dir(slug)
    return dump(
        {
            "slug": slug,
            "label": label_of(pin),
            "status": pin.get("status"),
            "jd_path": rel(jd_path(slug)),
            "pin_path": rel(pin_path(slug)),
            "triage_input_path": rel(dest / "triage_input.json"),
            "generated_hint": f"Generated/{slug}/",
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Per-role JD queue for parallel /tailor")
    sub = parser.add_subparsers(dest="command")

    ingest = sub.add_parser("ingest")
    ingest.add_argument("paths", nargs="*", type=Path)
    ingest.add_argument("--paste", action="store_true", help="Also ingest JobDescription.md")
    ingest.add_argument("--move", action="store_true", help="Delete inbox files after copy (never deletes JobDescription.md)")

    listing = sub.add_parser("list")
    listing.add_argument("--json", action="store_true")

    relabel = sub.add_parser("relabel")
    relabel.add_argument("slug", nargs="?")

    pin = sub.add_parser("pin")
    pin.add_argument("slug")

    verify = sub.add_parser("verify")
    verify.add_argument("slug", nargs="?")

    decide = sub.add_parser("decide")
    decide.add_argument("slug")
    decide.add_argument("decision", choices=sorted(DECISIONS))

    clear = sub.add_parser("clear")
    clear.add_argument("slug", nargs="?")

    iap = sub.add_parser("ingest-and-pin")
    iap.add_argument("--paste", action="store_true")
    iap.add_argument("--triage-input", type=Path)
    iap.add_argument("--source", type=Path)

    sub.add_parser("migrate-legacy")

    rename = sub.add_parser("rename")
    rename.add_argument("old")
    rename.add_argument("new")

    paths = sub.add_parser("paths")
    paths.add_argument("slug")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "ingest":
        paths = []
        for path in args.paths:
            paths.append(path if path.is_absolute() else ROOT / path)
        return cmd_ingest(paths or None, paste=args.paste, move=args.move)
    if args.command == "list":
        return cmd_list(as_json=args.json)
    if args.command == "relabel":
        return cmd_relabel(args.slug)
    if args.command == "pin":
        return cmd_pin(args.slug)
    if args.command == "verify":
        return cmd_verify(args.slug)
    if args.command == "decide":
        return cmd_decide(args.slug, args.decision)
    if args.command == "clear":
        return cmd_clear(args.slug)
    if args.command == "ingest-and-pin":
        triage_input = args.triage_input
        source = args.source
        if triage_input and not triage_input.is_absolute():
            triage_input = ROOT / triage_input
        if source and not source.is_absolute():
            source = ROOT / source
        return cmd_ingest_and_pin(paste=args.paste, triage_input=triage_input, source=source)
    if args.command == "migrate-legacy":
        return cmd_migrate_legacy()
    if args.command == "rename":
        return cmd_rename(args.old, args.new)
    if args.command == "paths":
        return cmd_paths(args.slug)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
