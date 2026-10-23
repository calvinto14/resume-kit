"""
lint_resume.py — Resume bullet format linter for LaTeX .tex files.

Checks every \\resumeItem{} against the bullet format rules:
  1. Exactly one sentence (no mid-bullet period starting a second sentence)
  2. No semicolons
  3. No em dashes (--- or Unicode —)
  4. Starts with a strong action verb (flags known weak openers)
  5. No content word repeated within the same bullet

Usage (run from the Resumes directory):
  python lint_resume.py "Generated/Google/Resume.tex"
  python lint_resume.py resumeSource.tex
  python lint_resume.py "Generated/Role/Resume.tex" --jd queue/<slug>/jd.md

The live resume (candidate_profile.json resume_basename) also requires the
sibling PDF (or --pdf). The page must be
exactly 1, and the last text baseline must sit at or below 110pt from the
bottom. A full baseline ends near 46pt. A three-quarter page fails this gate.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import zlib
from pathlib import Path

# Force UTF-8 output on Windows so emoji render correctly
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Words that are OK to repeat (domain keywords / technology names)
# ---------------------------------------------------------------------------
TECH_KEYWORDS = {
    "api", "apis", "rest", "sql", "go", "java", "python", "node", "react",
    "kubernetes", "aws", "azure", "docker", "ci", "cd", "tdd", "llm", "llms",
    "kafka", "postgresql", "postgres", "typescript", "javascript", "html",
    "css", "linux", "jenkins", "github", "spring", "grafana", "prometheus",
    "openapi", "yaml", "cli", "ux", "ui", "saas", "sas", "mosfet", "pandas",
    "jvm", "discovery", "monitoring", "grpc", "protobuf", "etl", "orchestration",
}

# ---------------------------------------------------------------------------
# Known weak / passive openings (lowercased for matching)
# ---------------------------------------------------------------------------
WEAK_OPENERS = [
    "familiar with",
    "responsible for",
    "worked on",
    "involved in",
    "participated in",
    "part of",
    "assisted with",
    "helped with",
    "helped to",
]

# ---------------------------------------------------------------------------
# Stop words excluded from repetition check
# ---------------------------------------------------------------------------
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "that", "this", "these", "those", "it", "its", "their", "they", "them",
    "not", "no", "nor", "as", "if", "so", "yet", "both", "each", "more",
    "most", "other", "some", "such", "than", "too", "very", "just", "across",
    "including", "improving", "reducing", "enabling", "providing", "cutting",
    "using", "leveraging", "delivering", "building", "making", "increasing",
    "within", "across", "between", "multiple", "overall", "well", "also",
}


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def strip_comments(tex_content: str) -> str:
    """Remove LaTeX comment lines (lines where first non-whitespace char is %)."""
    lines = tex_content.splitlines(keepends=True)
    cleaned = []
    for line in lines:
        if re.match(r"^\s*%", line):
            # Replace with a blank line to preserve line numbers
            cleaned.append("\n")
        else:
            cleaned.append(line)
    return "".join(cleaned)


def extract_resume_items(tex_content: str) -> list[tuple[int, str]]:
    """Return list of (line_number, raw_content) for every \\resumeItem{}."""
    items = []
    content = strip_comments(tex_content)
    pattern = re.compile(r"\\resumeItem\{")
    for match in pattern.finditer(content):
        start = match.end()
        depth = 1
        j = start
        while j < len(content) and depth > 0:
            if content[j] == "{":
                depth += 1
            elif content[j] == "}":
                depth -= 1
            j += 1
        raw_content = content[start : j - 1]
        line_num = content[: match.start()].count("\n") + 1
        items.append((line_num, raw_content))
    return items


def strip_latex(text: str) -> str:
    """Remove LaTeX markup, returning plain readable text."""
    # Unescape common LaTeX sequences first
    text = text.replace(r"\$", "$").replace(r"\%", "%").replace(r"\\", " ")
    # Replace \textbf{X} -> X, \textit{X} -> X, etc.
    text = re.sub(r"\\text\w+\{([^}]*)\}", r"\1", text)
    # Remove any remaining \command{arg} -> arg
    text = re.sub(r"\\\w+\{([^}]*)\}", r"\1", text)
    # Remove lone \command tokens
    text = re.sub(r"\\\w+", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_two_sentences(raw: str, plain: str) -> str | None:
    """Return a description of the violation if two sentences are detected."""
    # Pattern 1: '. \textbf{' in raw source (new sentence starting with bold word)
    if re.search(r"\.\s+\\textbf\{", raw):
        return "mid-bullet period before \\textbf{"

    # Pattern 2: '. Capital' in plain text — mask known false positives first
    text = plain
    # Mask decimal numbers like 1.7, 40.5
    text = re.sub(r"\d\.\d", lambda m: m.group().replace(".", "@"), text)
    # Mask common abbreviations
    text = re.sub(
        r"\b(e\.g|i\.e|etc|vs|mr|mrs|dr|jr|sr)\.",
        lambda m: m.group().replace(".", "@"),
        text,
        flags=re.IGNORECASE,
    )
    if re.search(r"\.\s+[A-Z]", text):
        # Find where
        m = re.search(r"\.\s+[A-Z]", text)
        snippet = text[max(0, m.start() - 20) : m.end() + 20]
        return f'mid-bullet period detected near "...{snippet}..."'

    return None


def check_semicolons(plain: str) -> bool:
    return ";" in plain


def check_em_dash(raw: str) -> bool:
    # '---' in LaTeX = em dash; Unicode em dash character
    return "---" in raw or "\u2014" in raw


def check_weak_opener(plain: str) -> str | None:
    lower = plain.lower().strip()
    for weak in WEAK_OPENERS:
        if lower.startswith(weak):
            return f'"{plain.split()[0]} {plain.split()[1] if len(plain.split()) > 1 else ""}..."'
    return None


def check_word_repetition(plain: str) -> dict[str, int]:
    """Return dict of {word: count} for content words repeated 2+ times."""
    words = re.findall(r"\b[a-z]{4,}\b", plain.lower())
    counts: dict[str, int] = {}
    for w in words:
        if w not in STOP_WORDS and w not in TECH_KEYWORDS:
            counts[w] = counts.get(w, 0) + 1
    return {w: c for w, c in counts.items() if c >= 2}


# ---------------------------------------------------------------------------
# Main linter
# ---------------------------------------------------------------------------

def check_section_order(tex_content: str):
    """Experience must appear before Skills (standing layout rule)."""
    exp = re.search(r"\\section\{Experience\}", tex_content)
    skills = re.search(r"\\section\{Skills\}", tex_content)
    if exp and skills and skills.start() < exp.start():
        return "SECTION ORDER: Skills appears before Experience — move Experience above Skills"
    return None


_BOLD_FILLER = re.compile(
    r"^(customers|pain points|self-service|successful|partial|unsupported)$",
    re.IGNORECASE,
)
_BOLD_METRIC = re.compile(
    r"(\d[\d,]*%|\$[\d.,]+[BMK]?|\d[\d,]*\+?\s*(daily|years?|engineers?)?)",
    re.IGNORECASE,
)


def _extract_textbf_spans(raw: str) -> list[str]:
    """Return inner text of each top-level \\textbf{...} (brace-balanced)."""
    spans: list[str] = []
    i = 0
    marker = r"\textbf{"
    while True:
        start = raw.find(marker, i)
        if start < 0:
            break
        j = start + len(marker)
        depth = 1
        while j < len(raw) and depth:
            if raw[j] == "{":
                depth += 1
            elif raw[j] == "}":
                depth -= 1
            j += 1
        spans.append(raw[start + len(marker) : j - 1])
        i = j
    return spans


def check_bold_spans(raw: str) -> str | None:
    """≤2 \\textbf spans/bullet; 3 allowed only if one span is a metric."""
    spans = _extract_textbf_spans(raw)
    n = len(spans)
    if n > 3:
        return f"TOO MANY \\textbf SPANS ({n}) — max 2 (3 if one is a metric)"
    if n == 3:
        if not any(_BOLD_METRIC.search(s) for s in spans):
            return "3 \\textbf SPANS without a metric span — keep ≤2 or bold a metric"
    filler = [s for s in spans if _BOLD_FILLER.match(s.strip())]
    if filler:
        return f"FILLER/ENUM \\textbf: {', '.join(repr(f) for f in filler)}"
    return None


# ---------------------------------------------------------------------------
# JD lexicon echo (optional --jd)
# ---------------------------------------------------------------------------

_JD_ECHO_RULES = [
    {
        "label": "REST",
        "jd_regex": r"\bREST(ful)?(\s+APIs?)?\b",
        "need_in_experience": r"\bREST\b",
        "skills_only_not_enough": True,
    },
    {
        "label": "gRPC",
        "jd_regex": r"\bgRPC\b",
        "need_in_experience": r"\bgRPC\b",
        "skills_only_not_enough": True,
    },
    {
        "label": "JavaScript",
        "jd_regex": r"\bJavaScript\b|\bJS/TS\b",
        "need_in_experience": r"\bJavaScript\b",
        "need_in_skills": r"\bJavaScript\b",
        "skills_only_not_enough": False,
    },
    {
        "label": "SQL",
        "jd_regex": r"\bSQL\b",
        "need_on_page": r"\bSQL\b",
        "skills_only_not_enough": False,
    },
    {
        "label": "ETL",
        "jd_regex": r"\bETL\b|\bELT\b|\bdata ingestion\b",
        "need_in_experience": r"\bETL\b",
        "need_in_skills": r"\bETL\b",
        "skills_only_not_enough": True,
    },
    {
        "label": "workflow orchestration",
        "jd_regex": r"\bworkflow orchestration\b",
        "need_in_experience": r"\bworkflow[- ]orchestration\b|\borchestrating\b",
        "skills_only_not_enough": True,
    },
]


def _section_plain(tex: str, heading: str) -> str:
    pattern = rf"\\section\{{{re.escape(heading)}\}}(.*?)(?=\\section\{{|$)"
    m = re.search(pattern, tex, flags=re.S | re.I)
    if not m:
        return ""
    return strip_latex(m.group(1))


def check_jd_lexicon(tex: str, jd_text: str) -> list[str]:
    """If the JD names REST/JVM/JS/SQL, those tokens must appear where recruiters look."""
    errors: list[str] = []
    experience = " ".join(strip_latex(raw) for _, raw in extract_resume_items(tex))
    skills = _section_plain(tex, "Skills")
    page = strip_latex(strip_comments(tex))
    for rule in _JD_ECHO_RULES:
        if not re.search(rule["jd_regex"], jd_text, flags=re.I):
            continue
        label = rule["label"]
        if rule.get("need_on_page") and not re.search(rule["need_on_page"], page, flags=re.I):
            errors.append(
                f"JD LEXICON: JD names {label} but the resume never says {label}"
            )
            continue
        if rule.get("need_in_skills") and not re.search(rule["need_in_skills"], skills, flags=re.I):
            errors.append(
                f"JD LEXICON: JD names {label} but Skills does not say {label}"
            )
        if rule.get("need_in_experience"):
            if not re.search(rule["need_in_experience"], experience, flags=re.I):
                where = "Skills-only" if re.search(rule["need_in_experience"], skills, flags=re.I) else "absent"
                errors.append(
                    f"JD LEXICON: JD names {label} but Experience bullets are {where} — "
                    f"echo {label} in the proof bullet, not Skills-only"
                )
    return errors


# A full page ends near 46pt. 110pt is about one inch of extra gap.
# Three-quarter pages end well above that.
MAX_BOTTOM_BASELINE_PT = 110.0

_PDF_OP = re.compile(
    r"([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s+([-+0-9.]+)\s+cm"
    r"|([-+0-9.]+)\s+([-+0-9.]+)\s+Td"
    r"|\[(?:\\.|[^\[\]])*\]\s*TJ"
    r"|\((?:\\.|[^\\)])*\)\s*Tj"
)


def _pdf_streams(data: bytes) -> list[str]:
    texts: list[str] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            texts.append(zlib.decompress(match.group(1)).decode("latin1", errors="ignore"))
        except zlib.error:
            continue
    return texts


def _pdf_page_count(texts: list[str]) -> int | None:
    for text in texts:
        match = re.search(r"/Type\s*/Pages\s*/Count\s+(\d+)", text)
        if match:
            return int(match.group(1))
    return None


def _min_text_baseline(text: str) -> float | None:
    """Lowest text baseline. pdftex uses an absolute Td, then small relative Tds."""
    y: float | None = None
    lows: list[float] = []
    for match in _PDF_OP.finditer(text):
        token = match.group(0)
        if token.endswith("cm"):
            y = float(match.group(6))
        elif token.endswith("Td"):
            dy = float(match.group(8))
            if y is None or dy > 30:
                y = dy
            else:
                y += dy
        elif y is not None:
            lows.append(y)
    return min(lows) if lows else None


def check_pdf_fill(pdf_path: Path) -> tuple[bool, str]:
    """Exactly one page, filled to the baseline. Returns (ok, message)."""
    if not pdf_path.is_file():
        return False, f"PAGE FILL: no PDF at {pdf_path}. Build with pdflatex, then re-run lint."
    data = pdf_path.read_bytes()
    streams = _pdf_streams(data)
    pages = _pdf_page_count(streams)
    lows = [y for y in (_min_text_baseline(text) for text in streams) if y is not None]
    if pages != 1:
        count = "unknown" if pages is None else str(pages)
        return False, f"PAGE FILL: expected 1 page, found {count}."
    if not lows:
        return False, "PAGE FILL: could not read text positions in the PDF."
    bottom = min(lows)
    if bottom > MAX_BOTTOM_BASELINE_PT:
        return (
            False,
            "PAGE FILL: last text baseline is "
            f"{bottom:.0f}pt from the bottom of the page. "
            f"A full page ends at or below {MAX_BOTTOM_BASELINE_PT:.0f}pt "
            "(the baselines end near 46pt). Add truthful bullets and rebuild.",
        )
    return True, f"PAGE FILL: 1 page, last baseline {bottom:.0f}pt (gate ≤{MAX_BOTTOM_BASELINE_PT:.0f}pt)."


def lint_file(filepath: str, jd_path: str | None = None, pdf_path: str | None = None) -> bool:
    """Lint a .tex file. Returns True if all bullets pass, False otherwise."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        return False

    content = path.read_text(encoding="utf-8")
    items = extract_resume_items(content)
    order_err = check_section_order(content)
    lexicon_errs: list[str] = []
    if jd_path:
        jd_file = Path(jd_path)
        if not jd_file.exists():
            print(f"ERROR: JD file not found: {jd_path}")
            return False
        lexicon_errs = check_jd_lexicon(content, jd_file.read_text(encoding="utf-8"))
    section_errors = (1 if order_err else 0) + len(lexicon_errs)

    def finish(bullets_ok: bool) -> bool:
        from kit_paths import load_profile, resume_basename

        measure = path.stem == resume_basename(load_profile(Path(__file__).resolve().parent))
        if not measure and not pdf_path:
            return bullets_ok
        pdf = Path(pdf_path) if pdf_path else path.with_suffix(".pdf")
        ok, msg = check_pdf_fill(pdf)
        mark = "✅" if ok else "❌"
        print(f"  {mark}  {msg}\n")
        return bullets_ok and ok

    if not items and not order_err:
        print(f"No \\resumeItem{{}} entries found in {filepath}")
        return finish(True)

    violations = []
    passed = 0

    for line_num, raw in items:
        plain = strip_latex(raw)
        issues: list[tuple[str, str]] = []  # (severity, message)

        # 1. Two sentences
        two_sent = check_two_sentences(raw, plain)
        if two_sent:
            issues.append(("❌", f"TWO SENTENCES — {two_sent}"))

        # 2. Semicolons
        if check_semicolons(plain):
            issues.append(("❌", "SEMICOLON found"))

        # 3. Em dash
        if check_em_dash(raw):
            issues.append(("❌", "EM DASH (---) found"))

        # 4. Weak opener
        weak = check_weak_opener(plain)
        if weak:
            issues.append(("❌", f"WEAK OPENING: {weak}"))

        # 5. Word repetition
        repeated = check_word_repetition(plain)
        if repeated:
            rep_str = ", ".join(f'"{w}" ({c}x)' for w, c in repeated.items())
            issues.append(("⚠ ", f"REPEATED WORDS: {rep_str}"))

        # 6. Bold skim (≤2 spans; no filler/enum crumbs)
        bold_err = check_bold_spans(raw)
        if bold_err:
            issues.append(("❌", bold_err))

        preview = (plain[:90] + "...") if len(plain) > 90 else plain

        if issues:
            violations.append({"line": line_num, "preview": preview, "issues": issues})
        else:
            passed += 1

    total = len(items)
    errors = sum(1 for v in violations for sev, _ in v["issues"] if sev == "❌") + section_errors
    warnings = sum(1 for v in violations for sev, _ in v["issues"] if sev == "⚠ ")

    print()
    print("=" * 65)
    print(f"  RESUME LINT REPORT")
    print(f"  File   : {path.name}")
    print(f"  Bullets: {total}   Passed: {passed}   Failed: {total - passed}")
    print(f"  Errors : {errors}   Warnings: {warnings}")
    print("=" * 65)

    if order_err:
        print(f"\n  ❌  {order_err}")
    for err in lexicon_errs:
        print(f"\n  ❌  {err}")

    if not violations and not order_err and not lexicon_errs:
        print("\n  ✅  All bullets passed!\n")
    else:
        for v in violations:
            print(f"\n  Line {v['line']}: \"{v['preview']}\"")
            for sev, msg in v["issues"]:
                print(f"    {sev}  {msg}")

    print()
    all_passed = errors == 0
    if all_passed and warnings > 0:
        print("  ✅  No errors. Review warnings above if needed.\n")
    elif not all_passed:
        print("  ❌  Fix errors before approving this resume.\n")
    return finish(all_passed)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lint a LaTeX resume.")
    parser.add_argument(
        "tex_path",
        nargs="+",
        help="Path to the .tex file (quote paths with spaces)",
    )
    parser.add_argument(
        "--jd",
        default=None,
        help="Optional JD markdown; errors if REST/JVM/JS/SQL are Skills-only or absent",
    )
    parser.add_argument(
        "--pdf",
        default=None,
        help="PDF to measure. Defaults to the sibling PDF when the .tex stem matches resume_basename.",
    )
    args = parser.parse_args()
    target = " ".join(args.tex_path)
    success = lint_file(target, jd_path=args.jd, pdf_path=args.pdf)
    sys.exit(0 if success else 1)
