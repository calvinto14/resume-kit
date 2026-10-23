# Tailor

Run this after `docs/setup.md` has finished. If `setup_complete` is not true, stop and set up first.

The live resume filename is `<resume_basename>.tex` from `candidate_profile.json`. Approved stories are `experience.md` and `resumeSource.tex`. Voice is `STYLE.md`. Read it before writing a bullet. Do not copy its fake examples.

Do the classify step and the judge step yourself, in this session, using the prompts named below. Then run the Python scripts. The scripts are the part that must not be approximated.

## Phase 0 — triage, then stop

```text
python compile_snapshot.py
python jd_queue.py ingest --paste --move
python jd_queue.py list --json
```

For each slot with `needs_classify: true`, follow `triage/classify_prompt.md`. Read `queue/<slug>/jd.md` and `snapshot.json`. Write only `queue/<slug>/triage_input.json`.

```text
python jd_queue.py relabel <slug>
python run_triage.py queue/<slug>/triage_input.json
```

Show one line and stop.

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

A rendered baseline copies `BaselineResumes/<archetype>/<resume_basename>.tex` into `Generated/<Role>/`, then `pdflatex` twice and lint. No judge.

## Phase 1 — only after they choose tailor

```text
python jd_queue.py decide <slug> tailor
python jd_queue.py verify <slug>
```

Tailor from `use_for_tailoring`. If `JobDescription.md` has changed, say so and keep the queued file.

1. Read `STYLE.md`. Pick `01-SWE`, `02-SWE-Adjacent`, `03-FDE`, or `04-GTM-Engineer`, and a strategy: `lateral`, `step-up`, `pivot`, or `reach`.
2. Reorder approved bullets and rewrite them in that voice. Echo lexicon `has` tokens in Skills and the proof bullet. Keep the outcome. Do not leave a stack-only line.
3. Bold at most two spans. First span is the artifact and stack. Second span is the metric.
4. Write `Generated/<Role>/<resume_basename>.tex`.
5. `pdflatex` twice, then `python lint_resume.py "<tex>" --jd queue/<slug>/jd.md`. Fix until one full page. Report the `PAGE FILL` line. Delete `.aux`, `.log`, and `.out`.
6. Follow `triage/judge_prompt.md` (`judge_and_plan`, iteration 1). If `should_auto_fix` is true, apply only that plan from approved sources, rebuild, and judge once more in `final_report_only`. Do not invent claims to raise the candidacy grade.
7. Write `notes.md` and `lesson.md`. Append the lesson to `Patterns/tailoring-lessons.md`.
8. Show both grades, then `python jd_queue.py clear <slug>`.

## Reply

After triage: the verdict line and the ask.

After a tailor: tex and pdf paths, page-fill line, archetype, strategy, gaps, and the judge grades.
