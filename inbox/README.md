# JD inbox

Drop job descriptions here as **`Company-Role.md`** (example: `Netflix-SWE5.md`).

`/tailor` (or a new-file hook) runs:

```text
python jd_queue.py ingest --move
```

That copies each file into `queue/<slug>/jd.md` and **moves** the inbox file out of the way (`JobDescription.md` is never deleted). Finished roles are **cleared from the queue**, not put back here.

Caps: **3 recommended, 5 max** in-flight slots.

**Event-driven:** `.cursor/hooks.json` runs `.cursor/hooks/inbox-tailor.py` on session start and after file edits. Opening or saving a JD in this folder should prompt the agent to ingest. Cursor cannot start a brand-new agent from a Finder paste alone — send a message or start a chat after dropping the file if the hook does not fire.
