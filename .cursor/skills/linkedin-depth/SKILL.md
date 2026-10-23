---
name: linkedin-depth
description: >-
  Drafts a longer LinkedIn reply that maps this person's real work to a job
  posting. Use when someone asks how they meet the role. Not a first-touch note.
---

# LinkedIn depth

**Model:** Claude Sonnet 5 (`claude-sonnet-5-thinking-high`), or inline if the parent already is.

If `setup_complete` is false, stop and run `/setup`.

If this is a first connection note, use `linkedin-outreach` instead.

Do not tailor a resume.

## Sources

- The posting they name
- `experience.md`, `candidate_profile.json`
- Their draft, if they pasted one. Keep their wording. Fix spelling. Do not replace their voice.

## Shape

1. How their work matches the way the role operates.
2. The requirements they meet, each tied to a section in `experience.md`.
3. The gaps on this posting, stated plainly, without a fix that invents experience.

No language-list opening. No claim the limits forbid. Tenure follows the profile dates, not the job's years floor.

Keep it short enough to paste. A few short paragraphs, not a memo.
