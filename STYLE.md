# House style

This is the writing voice for every resume, intro, and note this kit produces. It is a style, not a biography. Examples use fake employers and round numbers to show rhythm. Never copy an example's company, product, tool, or metric onto the person unless `experience.md` already contains it.

Read this before writing a sentence that lands on a PDF or in a spoken intro. For page shape, bold placement, and which story leads each role family, also read `templates/archetypes/`. Those files are patterns with empty brackets. They are not a person's experience.

## Resume bullets

One sentence. No semicolon. No em dash (`---`).

The shape is gap, thing built, change in the world:

**Identified a [specific gap] and built [the artifact (stack)]** so that [who] could [concrete change], [real outcome].

Use that opener when they found the problem and made the fix. Do not put it on every bullet. Other true shapes:

- **Designed and built [artifact (stack)]** for [the job it does], [outcome].
- **Authored** the design, **drove** the review, **coordinated** the people who had to agree, and **owned** the system. That is the delivery bullet. Do not write "Led end-to-end project delivery."
- **Engineered [tool (stack)]** that [a real person uses to do a job], [outcome].

The outcome is the point. A line that only names tools is not done.

Prefer about three lines on the page. If a fourth line is a repeated synonym, cut the synonym and keep the outcome. Do not shrink a three-line bullet to two if the outcome would disappear.

### Verbs and words to avoid

Do not open with: familiar with, responsible for, worked on, involved in, participated in, part of, assisted with, helped with, helped to, sought, leveraged, utilized, spearheaded, passionate about.

Do not write "AI-assisted" for work that was agents. Write **AI agents** and name the job they do (review, triage, a check before merge). Test-driven development is the person's practice. Do not write that agents ran it.

Do not write showcasing, recognition from experts, results-driven, or dynamic. Say what changed.

### Numbers

Use only numbers from `experience.md`. If they remembered the number instead of reading it off a dashboard, write **roughly** or **an estimated**. Use each number once on the page. The number has to be their work. A team goal they did not cause does not go in the bullet.

### Bold

At most two `\textbf` spans. A third is allowed only when one span is the metric.

- First span: the verb and the artifact, with the languages and tools inside it.
- Second span: the metric, or one product name.
- On a tailored resume, put the job description's own tool names and the impact it cares about inside those spans.
- Never bold filler: customers, pain points, self-service, successful, partial, unsupported.
- Do not bold every keyword. Skills carries the full list.

### Skills and header

Three or four lines, in this order: Languages, Frameworks/Libraries, Cloud/DevOps, then Interests if they named real ones.

Section order is Experience, Skills, Projects, Education.

The job's main language goes first in Languages. A framework the job names goes first in Frameworks. The cloud the story actually used goes first in Cloud. Other clouds stay in Skills.

If a React story truly used JavaScript and TypeScript, write `React (TypeScript/JavaScript)` in Frameworks and name JavaScript in the bullet. Do not expect a reader to infer JavaScript from the word React.

The title line is the title only. Do not append `| Python, Go`.

Header is phone, email, LinkedIn. No city. A city belongs on the job line, where the work happened.

### Lexicon

If `experience.md` maps a job-description word as something they have, use that word in Skills and in the proof bullet. A private synonym plus the keyword only in Skills is a miss.

If the map says they do not have it, leave the word off the page. Do not rename a nearby tool into the missing one.

If the job is in an industry they have not worked, keep the pattern (a pipeline, a review, a migration) and drop the industry word.

### Page and projects

One page, filled. A short page gets another approved story, not a vague line.

A project needs a number or a concrete outcome, or it comes off. Label a class project as a class project.

Interests stay when they are specific. One line.

## Rhythm examples

These are fake. Do not reuse them.

Good:

```text
Identified a visibility gap in a nightly import and built Python checks (PostgreSQL) that compared each run to the source of record, cutting repeat failures by roughly 30%.
```

Good:

```text
Designed and built a workflow service (Go, REST APIs, PostgreSQL) that let operators rerun a failed step without restarting the whole job, taking a typical recovery from hours to minutes.
```

Not done:

```text
Built Python, PostgreSQL, and cron to improve data quality for customers.
```

That line names tools and a filler noun. It never says what changed.

## Spoken and written voice

Friendly and straightforward. Short sentences that connect. Not a resume read aloud, and not a cover letter.

Default tone is professional but not stiff. Curious. No begging.

First person. Say what they did. Do not open by discounting themselves or listing what they are not.

No em dashes. No literary filler (`through-line`, `the real bar`, `I know you're looking for`).

### Intro

1. Who they are: name, title, how long, the kind of system they own.
2. What they do: the production work first, then the other thing they built, with three or four phrases from the job planted inside stories they can defend.
3. What led them here: that work points at a subject this company actually works on.
4. Why this role: the team and the work, not "I'm excited about the opportunity."

Skip any job phrase they cannot defend.

### Outreach

Ask about their work. Then a few sentences of true proof. If they already applied, say that in the last sentence.

One specific callback to their post is enough. Do not paraphrase the whole post.

### Application answers

One paragraph per question. Dense. No bullet list unless the form asks for a list.

## What this file will not do

It will not supply employers, titles, years, or metrics. Those come from `candidate_profile.json` and `experience.md`. Claim limits in `experience.md` win over any example here.
