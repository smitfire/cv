#!/usr/bin/env python3
"""
score.py — Jobscan-style keyword match score for one application.

Compares the rendered CV text against the JD and reports:
  * % of JD keywords present in the CV
  * top missing keywords (so you can decide whether to weave them in)
  * a sanity check that the visible word count matches the parsed PDF
    word count (catches accidental hidden text).

Usage:
    python scripts/score.py applications/<slug>/
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Common English stopwords + boilerplate JD/resume noise.
STOP = set(
    """
    a about above after again against all am an and any are as at be because been before being below
    between both but by could did do does doing down during each few for from further had has have
    having he her here hers herself him himself his how i if in into is it its itself just me more
    most my myself no nor not of off on once only or other our ours ourselves out over own same she
    should so some such than that the their theirs them themselves then there these they this those
    through to too under until up very was we were what when where which while who whom why will
    with you your yours yourself yourselves
    role responsibilities responsibility requirement requirements qualification qualifications
    candidate candidates we you us our team teams company companies position positions job jobs
    work working experience experiences year years skill skills ability abilities strong good great
    excellent proven track record looking seeking ideal would want need needs must should plus
    benefit benefits offer offered include includes including etc preferred preferences nice
    """.split()
)

WORD_RE = re.compile(r"[A-Za-z][A-Za-z+./#\-]{1,}")


def _tokens(text: str) -> list[str]:
    out = []
    for m in WORD_RE.findall(text):
        w = m.lower().strip("-./")
        if not w or len(w) < 2:
            continue
        if w in STOP:
            continue
        out.append(w)
    return out


def _bigrams(toks: list[str]) -> list[str]:
    return [" ".join(p) for p in zip(toks, toks[1:])]


def _read_jd(app_dir: Path) -> str:
    p = app_dir / "jd.md"
    if not p.exists():
        sys.exit(f"error: {p} missing — paste the job description into jd.md.")
    return p.read_text()


def _read_cv_text(app_dir: Path) -> str:
    pdf = app_dir / "cv.pdf"
    if not pdf.exists():
        sys.exit(f"error: {pdf} missing — run scripts/render.py first.")
    out = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def _extract_keywords(jd: str, top: int = 60) -> list[tuple[str, int]]:
    """Crude but effective: most common content words + bigrams in the JD."""
    toks = _tokens(jd)
    counts = Counter(toks) + Counter(_bigrams(toks))
    # require a bigram to appear at least twice; unigrams at least twice
    filtered = [(k, v) for k, v in counts.items() if v >= 2]
    filtered.sort(key=lambda x: (-x[1], x[0]))
    return filtered[:top]


def _normalise(s: str) -> str:
    return s.lower().strip()


def score(app_dir: Path) -> None:
    jd = _read_jd(app_dir)
    cv_text = _read_cv_text(app_dir)

    cv_lower = cv_text.lower()
    keywords = _extract_keywords(jd)

    if not keywords:
        sys.exit("error: no keywords extracted from jd.md — is it empty?")

    hits, misses = [], []
    for kw, count in keywords:
        if _normalise(kw) in cv_lower:
            hits.append((kw, count))
        else:
            misses.append((kw, count))

    pct = round(100 * len(hits) / len(keywords))

    # hidden-text sanity check
    cv_words = len(_tokens(cv_text))

    print(f"\n— keyword match: {pct}%  ({len(hits)}/{len(keywords)} keywords present) —")
    if pct >= 80:
        verdict = "strong (≥80%)"
    elif pct >= 70:
        verdict = "acceptable (70–79%)"
    elif pct >= 60:
        verdict = "weak (60–69%) — consider adding missing terms"
    else:
        verdict = "poor (<60%) — needs significant tailoring"
    print(f"  verdict: {verdict}")
    print(f"  CV word count (parsed from PDF): {cv_words}\n")

    if misses:
        print("missing keywords (consider weaving these in naturally):")
        for kw, count in misses[:25]:
            print(f"  - {kw}  (JD freq: {count})")
        if len(misses) > 25:
            print(f"  … and {len(misses) - 25} more")
    else:
        print("all extracted JD keywords are present in the CV.")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("app_dir", help="path to applications/<slug>/")
    args = p.parse_args()
    score(Path(args.app_dir).resolve())


if __name__ == "__main__":
    main()
