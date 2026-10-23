---
name: intro
description: >-
  Writes a spoken "tell me about yourself" from this person's approved
  experience. Use for /intro, TMAY, or an opening pitch for a job description.
---

# /intro

**Model:** Claude Sonnet 5 (`claude-sonnet-5-thinking-high`), or inline if the parent already is.

If `setup_complete` is false, stop and run `/setup`.

Write one spoken answer, about 60–90 seconds, in the first person. Default audience is a recruiter. If they say hiring manager, add one concrete system detail.

Do not tailor a resume.

## Sources

| File | Use |
|------|-----|
| The JD they name, or `JobDescription.md` | Phrases to weave in |
| `experience.md` | Stories and claim limits |
| `candidate_profile.json` | Name, title, tenure from the date math |

## Shape

1. Name, current or most recent title, how long, and the kind of work.
2. Two stories from `experience.md`, production work before side projects.
3. Three or four JD phrases they can actually claim, inside those stories.
4. Why this company and this role, tied to something the posting says.

Use `voice` from the profile when it is non-empty. No em dashes. No keyword list. No claim the limits forbid. Tenure comes from `years_math.py` logic and `stated_years`, not a round-up toward the job's years floor.
