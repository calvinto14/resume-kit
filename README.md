# Resume kit

This folder is a resume tailoring system with an empty profile. It runs in Claude Code, Cursor, or any other coding agent that can read the repo and run commands. The instructions live in `AGENTS.md` and `CLAUDE.md`, not in one product's skill folder.

Clone it, open the folder in Claude Code or Cursor, and say "set me up." Have your current resume ready to paste. The agent uses that resume as the facts. `templates/archetypes/*/sample.pdf` shows what a finished page sounds like. After the interview, paste a job description and say "tailor this."

## What you need installed

- Python 3.9 or newer
- A TeX install that provides `pdflatex` (MacTeX on macOS, TeX Live elsewhere)
- An agent that can edit files and run `python` and `pdflatex` in this folder. Claude Code reads `CLAUDE.md` on its own. Cursor reads `AGENTS.md` through the project rule.

No pip packages. Check readiness with:

```text
python doctor.py
```

Until setup finishes, that command exits 1. That is expected.

## First session

Say "set me up" and paste your current resume, or drop it at `inputs/resume.md`. `/setup` means the same thing. The interview checks what you would actually say. It does not paste your old bullets through unchanged, and it does not fill gaps from the sample patterns.

The interview is one topic at a time:

1. Name, phone, email, LinkedIn, work authorization
2. Jobs and school, with dates
3. Stories you can defend, including metrics you will actually say out loud
4. Skills, projects, and certificates
5. What the resume must never claim

It then writes `candidate_profile.json`, `experience.md`, `resumeSource.tex`, a one-page resume, and four orderings under `BaselineResumes/`. `python doctor.py` should exit 0 before you apply anywhere.

Have dates and a short list of projects ready. If you do not know a number, say so. The interview will not invent one.

## After setup

Paste one job description into `JobDescription.md`, or drop up to five `Company-Role.md` files in `inbox/`. Say "tailor this." `/tailor` means the same thing. In Claude Code, say that you added the file. Cursor can notice an inbox drop on its own.

You get a one-line fit verdict per role and a choice: `baseline <slug>` or `tailor <slug>`. Tailor writes `Generated/<Role>/` with a one-page PDF, notes, and a judge report that separates how the page reads from whether you are a fit.

Other commands, after setup:

| Say | Result |
|-----|--------|
| `/intro` | A spoken "tell me about yourself" for a posting |
| `/outreach` | A short LinkedIn note, after you answer a few questions |
| `/recruiter-questions` | Questions for a recruiter screen |

## How the system is shaped

The process is fixed. The writing voice is fixed too: `STYLE.md` is how bullets, intros, and notes are supposed to sound. The employers, dates, and metrics are yours. Setup will not copy the examples in that file onto your resume.

- `jd_queue.py` keeps each job description in its own slot (five at a time).
- A classify step labels requirements `has`, `adjacent`, or `missing` against `experience.md`.
- `years_math.py`, `knockout_check.py`, and `score_requirements.py` do the years, certification, and score math.
- Four baselines are the same stories in a different order: software engineer, solutions, forward deployed, and technical go-to-market.
- Tailoring may echo a job's wording only when your lexicon section says you have that work.
- `lint_resume.py` checks bullet shape and that the PDF is one full page.
- A judge grades packaging separately from candidacy, and may apply one packaging fix from sources you already approved.
- `Patterns/tailoring-lessons.md` starts with the standing rules and grows a log as you tailor.

## What not to put in this repo

Interview debriefs, old generated packets, and another person's bullets do not belong here. `templates/` is the blank set. Copying those files back over the live ones wipes your setup. Do that only on purpose.

## Share it

This directory is its own git repo, with no history from a personal resume. Commit and push it when you want someone else to clone it. They run `/setup` on their machine. They do not fill in your files.
