---
name: linkedin-outreach
description: >-
  Drafts a short LinkedIn note to a hiring manager from this person's own
  answers. Use for /outreach, InMail, or a connection note. Not a resume tailor.
---

# LinkedIn outreach

**Model:** Claude Sonnet 5 (`claude-sonnet-5-thinking-high`) for the draft. A fast model may only trim length after the thesis is locked.

If `setup_complete` is false, stop and run `/setup`.

Do not run `/tailor` or write `Generated/`.

## Shape

A genuine question about their work, then a few sentences of true background, then (if they already applied) that fact in the last sentence. Do not open with "I applied."

## Lane

Pick one: `SE`, `SWE`, `FDE`, or `GTM`. If it is unclear, ask.

| Lane | The note is about | Do not |
|------|-------------------|--------|
| SE | Customer problem and showing value | Invent a quota or an SE title they did not hold |
| SWE | What they ship, and why this product | Reuse a sales-engineering pitch |
| FDE | Building with the customer | Sound like a touring demo role when the job is embed |
| GTM | Technical delivery, enablement, or partnerships | Invent CRM, quota, or pipeline numbers |

## Intake

If they have not answered in this thread, ask and wait:

1. Who are you writing to, and which role?
2. What is one true proof from `experience.md` that matches that lane?
3. What do you actually want to ask them?
4. Did you already apply?

Draft only from those answers plus `experience.md` and the claim limits. Keep their wording when it is already clear.
