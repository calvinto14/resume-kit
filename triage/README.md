# Triage inputs

Phase 0 of `/tailor` classifies each role into an isolated **queue slot**, not a single shared pin.

```text
python jd_queue.py ingest --paste --move
python run_triage.py queue/<slug>/triage_input.json
python jd_queue.py verify <slug>
python jd_queue.py clear <slug>
```

| File | Purpose |
|------|---------|
| `inbox/*.md` | Batch drop (`Company-Role.md`) |
| `JobDescription.md` | One-JD paste buffer |
| `queue/<slug>/jd.md` | Pinned JD — **Phase 1 tailoring reads this** |
| `queue/<slug>/pin.json` | Title, company, content hash, status |
| `queue/<slug>/triage_input.json` | Classified `has / adjacent / missing` for that role |

`python jd_pin.py verify|clear|pin` still works as a wrapper. If more than one slot is in flight, pass the slug.

`triage/triage_input.json` may still exist from older runs; new work writes `queue/<slug>/triage_input.json`.

## Typical workflow

1. Paste a JD into `JobDescription.md` **or** drop up to 5 files in `inbox/`
2. `/tailor` → `compile_snapshot.py` → Gemini 3.8 Flash classifies each new slot from `snapshot.json` → scripts score/pin → one verdict line per slot (`PASS` / `BASELINE` / `FAIL`)
3. Reply `tailor <slug>`, `skip <slug>`, or `baseline <slug>` (bare `tailor` is ok if only one slot)
4. Phase 1 uses `queue/<slug>/jd.md`
5. After PDF build → **Phase 1c judge** → optional one auto-fix → final grade report → `jd_queue.py clear <slug>`
6. Other in-flight slots are untouched

Caps: **3 recommended, 5 max** in flight. PASS keepers run in parallel. Each writes `lesson.md`. Append lessons once after the batch. After `pdflatex`, `lint_resume.py` must pass the page-fill gate (1 page, last baseline ≤110pt).

## Model routing

| Step | Who |
|------|-----|
| Criteria extract + `has/adjacent/missing` | Gemini 3.8 Flash (`gemini-3.8-flash-high`) via `classify_prompt.md` — one Task per new slug |
| Years / knockout / score / pin | Scripts (`run_triage.py`, `jd_queue.py`) |
| Borderline re-judge when score flags escalate | Claude Opus 5 (`claude-opus-5-thinking-high`) — that slug only |
| Evidence card formatting | Parent (scored JSON → template). No Task. |
| Notes scaffolding, `.tex` typing, lint fixes | Composer 2.5 Fast (`composer-2.5-fast`) |
| Human ≠ suggested action | `python log_override.py … --slot <slug>` → `decision_overrides.md` |
| Post-tailor JD ↔ resume judge (iteration 1) | GPT-5.6 Sol (`gpt-5.6-sol-medium`) via `judge_prompt.md` → `Generated/<Role>/judge_report.{json,md}` |
| Apply fixable packaging plan (no new claims) | Composer 2.5 Fast + lint/pdflatex; max one fix cycle |
| Final judge (iteration 2) | `gemini-3.8-flash-high` or parent — not Opus |
| Phase 1a tailor voice (not a triage step) | Claude Sonnet 5 (`claude-sonnet-5-thinking-high`) — never downgraded |

Approved substitute for classify or judge: `grok-4.7-high-fast`. Never `composer-2.5-fast`, `muse-spark-1.3-high`, or `claude-fable-5-1-thinking-high` for labels or grades.

## Judge outputs

| File | Purpose |
|------|---------|
| `judge_prompt.md` | Judge instructions for packaging vs candidacy grades |
| `judge_report.example.json` | Schema for machine report |
| `Generated/<Role>/judge_report.md` | Human grade report (shown in delivery chat) |
| `Generated/<Role>/judge_report.json` | Machine plan + `should_auto_fix` |

Generated sidecar files (`*_knockout.json`, `*_scored.json`) next to a slot's `triage_input.json` are safe to delete after a run.

## v2 (deferred)

Chrome extension + localhost server to scrape JD from job pages into `inbox/` — not built yet; paste or drop files manually for now.
