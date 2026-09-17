#!/usr/bin/env python3
"""
review.py — validation cycle for one application.

Runs deterministic checks over tailored.yaml and the rendered CV / cover letter,
then writes review.md containing the results plus a critical-review rubric for
the reviewer (human or LLM) to complete before anything is sent.

Usage:
    python scripts/review.py applications/<slug>/
    python scripts/review.py applications/<slug>/ --threshold 75
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import yaml

import score as score_mod

ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILES = [
    ROOT / "source" / "profile.yaml",
    ROOT / "source" / "achievements_public.yaml",
    ROOT / "source" / "achievements_bank.yaml",
]

CLAIM_RE = re.compile(
    r"\d[\d,]*(?:\.\d+)?\s*(?:%|×|\+|\bGB\b|\bMB\b|\bKB\b|\bms\b|\bs\b|\bk\b|\bK\b|\bM\b|\bx\b)?"
)

YEAR_RE = re.compile(r"^(19|20)\d\d$")


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _claim_tokens(text: str) -> set[str]:
    out: set[str] = set()
    for m in CLAIM_RE.finditer(text):
        core = m.group(0).strip().replace(" ", "")
        digits = re.sub(r"[^\d]", "", core)
        if not digits or YEAR_RE.match(digits):
            continue
        distinctive = (
            "," in core
            or "%" in core
            or "×" in core
            or core.endswith("+")
            or core.endswith(("x", "GB", "MB", "KB", "ms", "k", "K", "M"))
            or len(digits) >= 3
        )
        if distinctive:
            out.add(core.lower())
    return out


def _load_yaml(path: Path):
    with path.open() as f:
        return yaml.safe_load(f)


def _corpus() -> str:
    parts = []
    for p in SOURCE_FILES:
        if p.exists():
            parts.append(p.read_text())
    return "\n".join(parts)


def _months(v) -> tuple[int, int] | None:
    if v is None:
        return None
    if isinstance(v, int):
        return (v, 12)
    if isinstance(v, (date, datetime)):
        return (v.year, v.month)
    m = re.match(r"^(\d{4})(?:-(\d{1,2}))?", str(v))
    if m:
        return (int(m.group(1)), int(m.group(2) or 12))
    return None


def _timeline_issues(experience: list) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    present_count = 0
    spans = []
    for e in experience:
        label = f"{e.get('company', '?')}"
        start, end = _months(e.get("start")), _months(e.get("end"))
        if str(e.get("end", "")).lower() == "present" or e.get("end") is None:
            present_count += 1
            end = None
        if start and end and start > end:
            errors.append(f"{label}: start {start} after end {end}")
        spans.append((label, start, end))
    if present_count > 1:
        errors.append(f"{present_count} roles marked present; expected 1")
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            a_label, a_start, a_end = spans[i]
            b_label, b_start, b_end = spans[j]
            if a_start and b_start and a_end and b_end and a_start < b_end and b_start < a_end:
                warnings.append(f"{a_label} and {b_label} overlap (by design?)")
    return errors, warnings


def _pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(str(path))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception:
        return ""


def _pdf_meta(path: Path) -> dict:
    try:
        import pikepdf
    except ImportError:
        return {}
    try:
        with pikepdf.open(str(path)) as pdf:
            return {str(k): str(v) for k, v in pdf.docinfo.items()}
    except Exception:
        return {}


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-.]*", text))


def review(app_dir: Path, threshold: int = 70) -> int:
    checks: list[tuple[str, str, str]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append((name, "PASS" if ok else "FAIL", detail))

    hard_errors: list[str] = []
    warnings: list[str] = []

    tailored_path = app_dir / "tailored.yaml"
    if not tailored_path.exists():
        print(f"error: {tailored_path} missing", file=sys.stderr)
        return 1
    tailored = _load_yaml(tailored_path)
    # meta and the cover letter carry addresses and dates, not CV claims.
    claim_source = {k: v for k, v in tailored.items() if k not in ("meta", "cover_letter")}
    authored = "\n".join(_strings(claim_source))
    meta = tailored.get("meta", {}) or {}

    required = ["jd.md", "cv.pdf", "cv.docx", "cv.html", "tailored.yaml"]
    missing = [f for f in required if not (app_dir / f).exists()]
    add("Required files", not missing, "missing: " + ", ".join(missing) if missing else "all present")
    if missing:
        hard_errors.append("missing files: " + ", ".join(missing))

    has_cover = bool(tailored.get("cover_letter"))
    cl_pdf = app_dir / "cover_letter.pdf"
    if has_cover and not cl_pdf.exists():
        hard_errors.append("cover_letter section present but cover_letter.pdf missing")
        add("Cover letter", False, "section present, PDF missing")
    elif has_cover:
        add("Cover letter", True, cl_pdf.name)
    else:
        warnings.append("no cover_letter section in tailored.yaml")
        add("Cover letter", True, "not requested")

    missing_meta = [k for k in ("company", "role_title", "jd_keywords") if not meta.get(k)]
    keywords = meta.get("jd_keywords") or []
    key_ok = not missing_meta and len(keywords) >= 10
    add(
        "JD metadata",
        key_ok,
        f"{len(keywords)} keywords" + (f", missing: {', '.join(missing_meta)}" if missing_meta else ""),
    )
    if missing_meta:
        hard_errors.append("meta missing: " + ", ".join(missing_meta))
    if not meta.get("source_url"):
        warnings.append("meta.source_url empty")

    jd = score_mod._read_jd(app_dir)
    cv_text = score_mod._read_cv_text(app_dir)
    cv_norm = score_mod._normalise(cv_text)
    kws = score_mod._extract_keywords(jd)
    hits = [k for k, _ in kws if score_mod._normalise(k) in cv_norm]
    pct = round(100 * len(hits) / len(kws)) if kws else 0
    misses = [(k, c) for k, c in kws if score_mod._normalise(k) not in cv_norm]
    add("JD keyword match", pct >= threshold, f"{pct}% ({len(hits)}/{len(kws)}), target {threshold}%")
    if pct < 60:
        hard_errors.append(f"keyword match {pct}% below hard floor 60%")
    elif pct < threshold:
        warnings.append(f"keyword match {pct}% below target {threshold}%")

    corpus = _corpus()
    corpus_tokens = _claim_tokens(corpus)
    claims = _claim_tokens(authored)
    untraceable = sorted(claims - corpus_tokens)
    add("Claim traceability", not untraceable, f"{len(claims)} claims, {len(untraceable)} untraceable")
    if untraceable:
        warnings.append(f"{len(untraceable)} numeric claims not found in source bank")

    dash_hits = []
    for s in _strings(tailored):
        for ch, name in (("—", "em dash"), ("–", "en dash")):
            if ch in s:
                dash_hits.append((name, s[:90]))
    add("Style: no em/en dashes in authored text", not dash_hits, f"{len(dash_hits)} occurrences")
    if dash_hits:
        warnings.append(f"{len(dash_hits)} em/en dash occurrences in authored text")

    placeholders = [p for p in ("TODO", "TBD", "lorem", "XXX", "{{", "}}") if p in authored]
    add("No placeholders", not placeholders, ", ".join(placeholders) if placeholders else "clean")
    if placeholders:
        hard_errors.append("placeholders found: " + ", ".join(placeholders))

    experience = tailored.get("experience", []) or []
    tl_errors, tl_warnings = _timeline_issues(experience)
    add("Timeline sanity", not tl_errors, "; ".join(tl_errors) if tl_errors else f"{len(experience)} roles")
    hard_errors.extend(tl_errors)
    warnings.extend(tl_warnings)

    html = (app_dir / "cv.html").read_text() if (app_dir / "cv.html").exists() else ""
    ats_flags = [t for t in ("<table", "display:none", "visibility:hidden", "#fff", "#ffffff", "font-size: 0") if t in html]
    add("ATS: single column, no hidden text", not ats_flags, ", ".join(ats_flags) if ats_flags else "clean")
    if ats_flags:
        hard_errors.append("ATS flags in cv.html: " + ", ".join(ats_flags))

    docinfo = _pdf_meta(app_dir / "cv.pdf")
    title = docinfo.get("/Title", "")
    doc_keywords = docinfo.get("/Keywords", "")
    meta_ok = bool(title) and bool(docinfo.get("/Author")) and len(doc_keywords) >= 20
    add("PDF metadata", meta_ok, f"title={title[:60]!r}, keywords={len(doc_keywords)} chars")
    if not meta_ok:
        warnings.append("cv.pdf metadata incomplete")

    cv_words = _word_count(cv_text)
    cv_len_ok = 450 <= cv_words <= 1300
    add("CV length", cv_len_ok, f"{cv_words} words (sane range 450-1300)")
    if not cv_len_ok:
        warnings.append(f"CV word count {cv_words} outside 450-1300")

    if has_cover:
        cl_text = _pdf_text(cl_pdf)
        cl_words = _word_count(cl_text)
        company = str(meta.get("company", ""))
        role_title = str(meta.get("role_title", ""))
        cl_ok = 140 <= cl_words <= 500 and company.split()[0].lower() in cl_text.lower()
        detail = f"{cl_words} words"
        if company and company.split()[0].lower() not in cl_text.lower():
            detail += f", missing company name {company!r}"
        add("Cover letter content", cl_ok, detail)
        if not cl_ok:
            warnings.append("cover letter length or company mention issue")
        if role_title and role_title.split()[0].lower() not in cl_text.lower():
            warnings.append("cover letter does not name the role")

    status = "FAIL" if hard_errors else ("PASS WITH WARNINGS" if warnings else "PASS")
    slug = app_dir.name
    lines = [
        f"# Review — {meta.get('company', slug)} · {meta.get('role_title', '')}".rstrip(),
        "",
        f"- Date: {date.today().isoformat()}",
        f"- Application: `{slug}`",
        f"- Status: **{status}** ({len(hard_errors)} errors, {len(warnings)} warnings)",
        "",
        "## Automated checks",
        "",
        "| Check | Result | Detail |",
        "|-------|--------|--------|",
    ]
    for name, result, detail in checks:
        lines.append(f"| {name} | {result} | {detail.replace('|', '/')} |")

    if hard_errors:
        lines += ["", "## Errors (must fix)", ""] + [f"- {e}" for e in hard_errors]
    if warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in warnings]

    if untraceable:
        lines += ["", "## Untraceable numeric claims", ""]
        for tok in untraceable:
            idx = authored.lower().find(tok)
            ctx = authored[max(0, idx - 60): idx + 60].replace("\n", " ") if idx >= 0 else ""
            lines.append(f"- `{tok}` ... {ctx.strip()}")

    if misses:
        lines += ["", "## Missing JD keywords (top 15)", ""]
        for kw, count in misses[:15]:
            lines.append(f"- {kw} (JD freq: {count})")

    # Re-renders must not discard a completed critical review.
    critical = None
    out = app_dir / "review.md"
    if out.exists():
        old = out.read_text()
        idx = old.find("## Critical review")
        if idx != -1:
            critical = old[idx:]
    if critical is None:
        critical = "\n".join(
            [
                "## Critical review (complete before sending)",
                "",
                "Answer each line, then set the verdict. Be adversarial: this is a red-team pass, not a cheerleader pass.",
                "",
                "1. Positioning: does the top third (headline + summary + first role) answer why this candidate for this role?",
                "2. JD coverage: does every need-to-have in the JD map to specific evidence, in the JD's own vocabulary?",
                "3. Evidence quality: is every claim verifiable, correctly attributed, and free of inflation?",
                "4. Gaps and risks: what is missing, weak, or likely to be probed at interview or on a trial day?",
                "5. Cover letter: specific to this company and role, or generic? Any repeated CV phrasing?",
                "6. Would the recruiter reply with a yes? If not, what is the single highest-impact change?",
                "",
                "Verdict: **SHIP** / **REVISE** (delete the one that does not apply)",
                "",
                "Reviewer notes:",
                "",
            ]
        )

    lines += ["", critical.rstrip(), ""]
    out.write_text("\n".join(lines) + "\n")

    print(f"\nreview [{status}]: {len(hard_errors)} errors, {len(warnings)} warnings")
    print(f"  keyword match {pct}%, CV {cv_words} words")
    print(f"  wrote {out}")
    if hard_errors:
        for e in hard_errors:
            print(f"  ERROR: {e}", file=sys.stderr)
    return 1 if hard_errors else 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("app_dir", help="path to applications/<slug>/")
    p.add_argument("--threshold", type=int, default=70, help="keyword match target (default 70)")
    args = p.parse_args()
    app_dir = Path(args.app_dir).resolve()
    if not app_dir.is_dir():
        sys.exit(f"error: {app_dir} is not a directory")
    sys.exit(review(app_dir, threshold=args.threshold))


if __name__ == "__main__":
    main()
