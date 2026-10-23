# Triage classification prompt

Do this in the current session. Any capable model may run it. Do not stop because a particular product or model name is unavailable.

**Calibration:** bias toward `missing`. A generous `has` inflates the tailor that follows. If you cannot point at a file and section, the label is `missing`.

Use this for criteria extraction and fit labels only. Do not run gate scripts, write `Generated/`, or tailor.

## Inputs

1. The JD path in the task (`queue/<slug>/jd.md`)
2. `snapshot.json` (bullets, lexicon, archetype notes, profile). Run `python compile_snapshot.py` first if it is missing. Do not read `Patterns/tailoring-lessons.md` on this pass.
3. `triage/triage_input.example.json` (output schema)

Open `experience.md` only to confirm a `has` or `adjacent` citation that is not already in the snapshot.

If `candidate_profile.json` has `setup_complete: false`, stop and say to run `/setup`. Do not classify a placeholder profile.

## Rules

- Truth only from approved sources. Never invent skills, metrics, tools, or titles.
- Qualifiers: `must` / `required` / `minimum` → `required`. `preferred` / `nice-to-have` / `bonus` → `preferred`.
- Extract **5–10 required** and **3–5 preferred** criteria.
- Each criterion needs a short quoted JD span.
- Status: `has` | `adjacent` | `missing`.
  - `has` — direct, interview-defendable proof
  - `adjacent` — related proof that would need careful wording
  - `missing` — no truthful claim, or you are unsure
- Every `has` / `adjacent` evidence line names the source section.
- Include `years_required` (number or `null`) and `years_level` (`required` | `preferred`).
- Copy `work_authorization_ok` from the profile. Do not assume `true` when it is null.
- If `ignore_location` is true, do not add city, onsite, hybrid, relocation, commute, or timezone to knockouts or skip rationale. Work authorization can still knock out.
- Do not put the JD city on the resume header.

## Output

Write only `queue/<slug>/triage_input.json` (or the path the task names):

```json
{
  "jd": {"title": "...", "company": "...", "link": "..."},
  "years_required": null,
  "years_level": "required",
  "required_floor_ratio": 0.7,
  "knockout": {
    "work_authorization_ok": true,
    "certifications_required": [],
    "certifications_held": [],
    "other_knockouts": []
  },
  "criteria": [
    {
      "requirement": "...",
      "level": "required",
      "status": "has",
      "evidence": "experience.md §1"
    }
  ],
  "lexicon_map": [
    {
      "jd_token": "REST",
      "status": "has",
      "source_proof": "experience.md lexicon",
      "echo_in": "Skills and the proof bullet"
    }
  ],
  "bullet_map": [
    {"jd_priority": "...", "proof_bullet": "...", "source": "experience.md §1"}
  ],
  "archetype_hint": "01-SWE | 02-SWE-Adjacent | 03-FDE | 04-GTM-Engineer",
  "strategy_hint": "lateral | step-up | pivot | reach",
  "notes_for_card": "one line"
}
```

`lexicon_map`: 5–12 rows. `has` means echo the JD token on the page. `adjacent` means pattern language, not the domain word. `missing` means leave it off. Bias to `missing` when the word would imply a domain the claim limits forbid.

`bullet_map`: top 3 JD priorities mapped to existing bullets. Select and reorder only.

Archetypes:

- `01-SWE` — individual contributor engineering
- `02-SWE-Adjacent` — solutions, sales engineering, solutions architect, demo-led forward deployed
- `03-FDE` — production embed: build and deploy with the customer. Map build stories first, not decks.
- `04-GTM-Engineer` — technical GTM, applications, partnerships, implementation

`strategy_hint`: `lateral` same shape of work, `step-up` more scope, `pivot` a real lane change with transferable proof, `reach` a hard gap remains.

## Borderline re-judge

If the person asks you to re-check a borderline slug, only re-classify the listed criteria. Prefer `missing` unless the evidence is explicit. A second model is optional.

## Done

Valid JSON at the task path. No evidence card, no `run_triage.py`, no PDF.
