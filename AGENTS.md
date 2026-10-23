# Agent instructions

This repo is harness-agnostic. Cursor, Claude Code, Claude in a project, or any other coding agent follows this file. Do not wait for a slash command, a Cursor skill, or a second product's model picker. If the person says "set me up", "/setup", "tailor this", or pastes a job description, start the matching section below.

Python and `pdflatex` do the mechanical checks. You do the interview, the fit labels, the wording, and the judge. Run those in the current session. A missing model name is not a reason to skip a step.

## Read before writing

| When | Read |
|------|------|
| Always, before a bullet, intro, or note | `STYLE.md` |
| First run, or `doctor.py` is not ready | `docs/setup.md` |
| A job description | `docs/tailor.md`, then `triage/classify_prompt.md` and, after a tailor, `triage/judge_prompt.md` |
| Intro, LinkedIn, or recruiter questions | `docs/voice.md` |

`STYLE.md` is the voice. Its examples are fake. Claim limits in `experience.md` win.

## Gate

Run `python doctor.py`. If `candidate_profile.json` has `setup_complete` false, follow `docs/setup.md` and stop. Do not tailor the placeholder resume.

## What the person says

| They say | You do |
|----------|--------|
| Set me up, `/setup`, first run | `docs/setup.md` |
| Here is a job, tailor this, `/tailor` | `docs/tailor.md` Phase 0, then stop for their decision |
| `baseline <slug>` or `tailor <slug>` | That decision only. Do not re-read a newer paste as the job. |
| Tell me about yourself, `/intro` | `docs/voice.md` intro |
| LinkedIn note, `/outreach` | `docs/voice.md` outreach |
| How I meet this role | `docs/voice.md` depth reply |
| What should I ask the recruiter | `docs/voice.md` recruiter questions |

Inbox files are noticed automatically only in Cursor. Everywhere else, the person says they dropped a file, and you ingest it the same way.

Never submit an application for them.
