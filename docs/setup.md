# Setup

The person brings their own resume. You interview them until every claim is one they would say out loud, then you rewrite it in `STYLE.md` using `templates/archetypes/` for shape and order.

Do not tailor a job description in this step. Ask one round per turn. Wait for the answer.

Read `templates/archetypes/*/sample.pdf` when you need to hear a finished page. Do not copy its name, employers, metrics, or stories onto this person. Their resume and the interview are the only source of facts.

## Start

1. Run `python doctor.py`.
2. Read `candidate_profile.json`, `experience.md`, `STYLE.md`, and `templates/README.md`.
3. If `setup_complete` is already true, ask which part to update. Do not overwrite files until they say so.

## Round 0 — their resume

Ask them to paste their current resume or drop the file at `inputs/resume.md` (PDF text pasted into that file is fine). `inputs/` is gitignored so the original resume is not pushed.

Read the whole thing. Extract employers, titles, dates, locations, bullets, skills, projects, school, and contact details. Note anything that looks like a team result stated as a personal one, a metric with no source, or a skill that never appears in a story.

Show a short inventory: roles, and one line per story. Ask which stories are real and which should come off. Do not rewrite the PDF yet.

If they have no resume, skip to round 1 and build the inventory from the interview only.

## Round 1 — identity

Confirm what the resume already has. Ask only for what is missing or wrong.

- Full name, as it should appear on the resume
- Phone, email, LinkedIn URL
- Whether they are authorized to work for the jobs they will apply to (`work_authorization_ok` true or false). Do not store visa documents or document numbers.
- Confirm the default: job location, onsite, hybrid, and relocation are not knockouts (`ignore_location` true). They can turn that off.

Do not put a city in the contact line.

## Round 2 — jobs and school

Read dates back from their resume. Correct anything they dispute. For each job: employer, title, city and region for that job line, start `YYYY-MM`, end `YYYY-MM` or present, and whether it counts toward years of relevant experience.

Then education: school, degree, location, dates if they want them.

Read the list back. Ask them to correct dates before the next round.

## Round 3 — stories

Walk their resume bullets one at a time. For each one, ask what they personally did, what the team did, and whether the number is something they can defend. Take several turns if needed. Capture:

- What they built or did
- Stack, in their words
- What they personally did versus the team
- A metric they can defend, or an explicit "no number"
- What a skeptical interviewer would challenge

After each story, restate it in one sentence and ask "would you say that out loud?" If they hesitate, cut it or remove the number.

Aim for enough material to fill one page: about 8–12 bullets for the main role when the career supports it, plus earlier roles and one project. If the career is shorter, fewer honest bullets are correct. Do not invent filler. Ask for another real story instead.

## Round 4 — skills, projects, certificates

- Languages, frameworks, and cloud they have used in the stories
- One or two projects outside the jobs, with an outcome, or none
- Certificates held. Anything in progress is `certifications_pursuing` and must not appear as a credential.
- Skills they are studying: `studied_skills`, with a note that they are not production experience
- Interests, optional, one line

## Round 5 — limits and voice

- Domains, tools, and titles they must not claim
- A few sentences in their own voice, or permission to match the way they described the stories
- Which role families matter right now: SWE, solutions or SE, forward deployed, GTM or partnerships

## Write, only after they confirm the story list

Draft every bullet in the voice of `STYLE.md`. Use `templates/archetypes/01-SWE/pattern.tex` and the other three pattern files for clause order, bold placement, and which story type leads each archetype. Fill a bracket only from their resume plus this interview. If they have no story for a bracket, delete that bullet. Do not keep a bracket, and do not borrow a tool or metric from the pattern.

Show them each sentence. If they would not say it out loud, rewrite it from their words.

1. `candidate_profile.json` with `setup_complete: true`, `full_name`, `resume_basename` (the name, no `.tex`), header, employment, education, certs, voice, and work authorization.
2. `experience.md`:
   - Remove the "not set up" status.
   - `## JD lexicon echo` with tokens they can honestly echo, status, proof, and where it belongs on the page.
   - `## Claim limits` including every "do not claim" from round 5.
   - `## 1.` onward, one section per story, with the approved bullet sentence and the interview note under it.
3. `resumeSource.tex`: the bullet library, one `\resumeItem` per approved bullet. It may run past one page.
4. Root `<resume_basename>.tex` and the four baseline copies. Same approved bullets, different order. Follow `BaselineResumes/*/notes.md` and the matching `templates/archetypes/*/pattern.tex`. Rename files if the basename changed, and delete the old `Resume.tex` copies. Leave the pattern files untouched.
5. `python compile_snapshot.py`
6. `pdflatex` twice on the root resume and each baseline. `python lint_resume.py` on each live resume file. Delete `.aux`, `.log`, `.out`.
7. If the page is short, go back to round 3 for another real story. If it is two pages, cut the weakest approved bullet and rebuild.
8. `python doctor.py` must exit 0.

Show them the PDF path and the claim limits. The next step is to paste a job description and ask to tailor it.

## Hard rules

- Never suggest a plausible percentage, revenue number, or customer count.
- Never upgrade "studied" or "used once" into production experience.
- Never copy another person's resume into this repo.
- A reset copies `templates/candidate_profile.json`, `templates/experience.md`, and `templates/resume.tex` back over the live files only after they explicitly confirm. Do not copy `templates/archetypes/` onto the live resume.
