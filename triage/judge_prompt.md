# Post-tailor judge prompt

Do this in the current session after the PDF exists. Any capable model may run it. Never skip this step because a particular product or model name is unavailable. A second pass after an auto-fix is still required. Do not raise the grade by inventing experience.

**Calibration:** grade inflation makes this step worthless. A lenient packaging grade with `should_auto_fix: false` launders a weak resume. Every finding quotes a resume line or a JD span. If you cannot cite it, drop it.

Run this after Phase 1 has a one-page tailored `.tex`. Do not clear the queue slot. Do not re-triage unless a packaging miss contradicts an approved source.

## Inputs

1. Pinned JD from `python jd_queue.py verify <slug>` (`use_for_tailoring`)
2. The tailored `.tex` under `Generated/<Role>/` (basename from `candidate_profile.json`)
3. `Generated/<Role>/notes.md`
4. `queue/<slug>/triage_input.json`
5. `snapshot.json`. Open `experience.md` only to confirm a bullet the snapshot does not already contain.
6. `triage/judge_report.example.json`

## Two grades

| Grade | Question |
|-------|----------|
| **packaging_grade** | Given approved sources only, how well does this PDF sell the real match? |
| **candidacy_grade** | How hireable is this person for this JD after perfect packaging? |

Letter scale: A / A- / B+ / B / B- / C+ / C / C- / D / F.

`overall_verdict` is one line, for example `strong packaging / reach candidacy`.

- Do not inflate candidacy because the page looks good.
- Do not tank packaging because years or a missing tool are absent. Those are unfixable.
- If `ignore_location` is true, location does not change candidacy and is not an unfixable gap.
- If the JD names a token the lexicon maps as `has`, packaging cannot be A or A- when that token is missing or Skills-only.
- Grade against `STYLE.md`. A stack-only bullet, a missing outcome, a filler bold, a weak opener, or an em dash is fixable packaging. Do not treat the fake examples in `STYLE.md` as approved experience.

## Findings

| `kind` | Meaning | Auto-fix? |
|--------|---------|-----------|
| `fixable_packaging` | Reorder, restore an approved bullet, echo a mapped token, cut redundancy, fix section order or bold skim | Yes, if planned |
| `unfixable_gap` | Not in approved sources, years floor, missing cert | No |
| `voice_risk` | Wording that may fail an interview | No, unless a safer approved sentence already exists |

## Auto-fix plan

- At most 5 items.
- Each item cites the JD signal, the approved source, and the exact change.
- Forbidden: new tools, inflated years, fake titles, new domains, new metrics.
- If packaging is already B+ or higher and the rest is polish, set `should_auto_fix` false.
- If packaging is B or lower because of fixable misses, set `should_auto_fix` true.

The parent applies at most one auto-fix, then a final judge with `mode: final_report_only`. Set `iteration` to 1 or 2.

## Output

Write both `Generated/<Role>/judge_report.json` and `judge_report.md`.

```markdown
# Judge report — <Company> · <Role>

**Iteration:** 1 | 2 (final)
**Packaging grade:** <letter> — <one line>
**Candidacy grade:** <letter> — <one line>
**Overall:** <verdict>

## What’s working
- ...

## Fixable packaging gaps
1. ...

## Unfixable ceilings
1. ...

## Auto-fix plan
- [ ] ...

## Eye-flow / Skills checks
- 6-second skim: pass | fail — ...
- Named languages: pass | fail — ...
- JD lexicon echo: pass | fail — ...
- Archetype texture: pass | fail | n/a — ...
- Section order: pass | fail — ...
- Bold skim: pass | fail — ...
```

Return packaging grade, candidacy grade, whether to auto-fix, and the top three findings.

## Done

Both report files exist. No fabricated claims in the plan. No queue clear and no `pdflatex` in this step.
