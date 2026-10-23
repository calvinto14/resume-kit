---
name: tailor
description: >-
  Triage then tailor the resume in this repo. Phase 0 ingests JobDescription.md
  and inbox/*.md into queue slots (max 5). Phase 1 uses queue/<slug>/jd.md
  after the user says tailor <slug>. Requires /setup first.
---

# Tailor resume

## Before anything else

Read `candidate_profile.json`. If `setup_complete` is not true, stop and follow the **setup** skill. Do not classify or tailor `Resume.tex` while it is still the placeholder.

The live resume filename is `<resume_basename>.tex` from that profile. The approved stories are `experience.md` and `resumeSource.tex`.

## Model routing

| Tier | Slug | Use |
|------|------|-----|
| Fast judgment | `gemini-3.8-flash-high` | Classify; iteration-2 judge |
| Critique | `gpt-5.6-sol-medium` | Iteration-1 judge |
| Voice | `claude-sonnet-5-thinking-high` | Phase 1a wording |
| Judgment+ | `claude-opus-5-thinking-high` | Borderline re-judge; contested 02 vs 03 |
| Mechanical | `composer-2.5-fast` | Typing `.tex`, lint fixes, applying an auto-fix plan |
| Scripts | none | Queue, years, knockout, score, snapshot, lint, PDF |

`grok-4.7-high-fast` may substitute for classify or judge. Never use the mechanical model to set fit labels or grades. Never downgrade Phase 1a.

## Commands

| User says | Action |
|-----------|--------|
| `/tailor`, `new JD`, `tailor this` | Phase 0, then stop |
| `skip`, `baseline`, or bare `tailor` after one verdict | That decision for the single in-flight slot |
| `tailor <slug>` / `skip <slug>` / `baseline <slug>` | That slot only |
| `tailor and proceed` in the same message as a new JD | Phase 0, then Phase 1 |

## Phase 0

```text
python compile_snapshot.py
python jd_queue.py ingest --paste --move
python jd_queue.py list --json
```

Classify each slot with `needs_classify: true` using `triage/classify_prompt.md`. The classifier reads `queue/<slug>/jd.md` and `snapshot.json` and writes only `queue/<slug>/triage_input.json`.

Then:

```text
python jd_queue.py relabel <slug>
python run_triage.py queue/<slug>/triage_input.json
```

Show one verdict line and stop.

```text
## <Company> — <Role>
PASS|BASELINE|FAIL  <archetype>  N has / N adjacent / N missing  years ok | years A vs B
Slug: `<slug>`
```

PASS is 85%+ required fit and no knockout. 55–85% is BASELINE. Knockout or under 55% is FAIL.

Ask for `baseline <slug>` or `tailor <slug>`. Clear every FAIL unless they promote it.

On skip or baseline:

```text
python jd_queue.py decide <slug> skip|baseline
python jd_queue.py clear <slug>
```

If their choice differs from `suggested_action`:

```text
python log_override.py --suggested <action> --chosen <action> --why "..." --slot <slug>
```

A baseline they want rendered is a copy of `BaselineResumes/<archetype>/<resume_basename>.tex` into `Generated/<Role>/`, then `pdflatex` twice and lint. No judge.

## Phase 1

```text
python jd_queue.py decide <slug> tailor
python jd_queue.py verify <slug>
```

Tailor from `use_for_tailoring`. If `JobDescription.md` has changed, say so and keep the queued file.

1. Pick the archetype and a strategy: `lateral`, `step-up`, `pivot`, or `reach`.
2. Reorder approved bullets. Echo lexicon `has` tokens in Skills and the proof bullet.
3. Bold at most two spans. Prefer the JD's tool names and the metric.
4. Write `Generated/<Role>/<resume_basename>.tex`.
5. `pdflatex` twice, then `python lint_resume.py "<tex>" --jd queue/<slug>/jd.md`. Fix until one full page. Report `PAGE FILL`. Delete aux, log, and out files.
6. Judge with `triage/judge_prompt.md` (`judge_and_plan`, iteration 1). If `should_auto_fix` is true, apply only that plan, rebuild, and judge once more in `final_report_only`. Do not invent claims to raise the candidacy grade.
7. Write `notes.md` and `lesson.md`. Append the lesson to `Patterns/tailoring-lessons.md`.
8. Show both grades, then `python jd_queue.py clear <slug>`.

Never auto-submit.

## Final reply

After triage: the verdict line and the ask.

After a tailor: tex and pdf paths, page-fill line, archetype, strategy, gaps, and the judge grades.
