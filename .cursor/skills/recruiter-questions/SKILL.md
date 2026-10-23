---
name: recruiter-questions
description: >-
  Writes recruiter-screen questions from a job description. Use for
  /recruiter-questions or "what should I ask" on a recruiter call.
---

# /recruiter-questions

**Model:** Claude Sonnet 5, or the parent once the role family is clear. This is a short list, not a resume.

If `setup_complete` is false, stop and run `/setup`.

If no JD is attached, ask which file. Do not invent the company's strategy.

Write **7 questions** a recruiter can answer, then **2–3** to save for the hiring manager.

## What a useful question does

- Asks where the week actually goes
- Asks how this posting differs from a sibling req with a similar title
- Asks level, process, and what "senior" means on this team
- Uses a real gap from `experience.md` only to decide fit, not to apologize

Skip culture, "what does success look like" with no context, and questions the recruiter cannot know (architecture ownership, internal politics).

Order: how the seat spends time, how this req differs from neighbors, level and process, then one question that uses their background. Park architecture and adoption for the hiring manager.

No em dashes. Write the questions the way this person would say them.
