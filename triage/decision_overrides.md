# Decision overrides log

Append one row whenever the human chooses differently from the script `suggested_action`.

```text
python log_override.py --suggested skip --chosen tailor --why "One-line reason" --slot <slug>
```

## Schema

| Field | Meaning |
|-------|---------|
| date | ISO date |
| label | Company · Role |
| suggested | skip \| baseline \| tailor |
| chosen | skip \| baseline \| tailor |
| why | One short reason |
| borderline | yes \| no |
| required_fit | e.g. has 4 / adj 2 / miss 1 |

## Log

| date | label | suggested | chosen | why | borderline | required_fit |
|------|-------|-----------|--------|-----|------------|--------------|
