#!/usr/bin/env python3
"""
One-off polish pass on every applications/*/tailored.yaml:

  1. Replace the "two prior exits, one undisclosed" claim with the cleaner
     "exit at RTK.io / Magnite as 1st technical hire" framing (everywhere it appears).
  2. Pull in-CV gap acknowledgments out of the body — those belong only in the cover
     letter. Specific scrubs:
       - Cerrion's "Recent AI/ML work has been LLM- and embedding-focused..." sentence
       - MKS PAMP's "Note: my primary backend is Python..." sentence in summary
       - Stellium's French/Power-Platform/cert apologies in summary
       - Corintis's "(12+ yrs senior industry experience compensates for the Master's-preferred ask in the JD)" parenthetical in education
       - rjc-group's "(worked at EPFL, not an EPFL alumnus)" role suffix and "B.Sc. — note: ..." education annotation
       - Google's "given my background I'd be a stronger fit at L5..." softening
  3. Promote SQL / testing / DevOps / AI-tooling more visibly when summary is short on those.

Idempotent — safe to re-run.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPS = ROOT / "applications"


# ---- universal scrubs (apply across all tailored.yamls) -----------------------------

UNIVERSAL = [
    # YAML folded scalars (`> `) join lines with spaces, so we need re.DOTALL-ish behaviour.
    # Use \s+ between words to tolerate either a single space or a newline+indent.
    (
        re.compile(r'Two\s+prior\s+exits\s+as\s+1st\s+engineer\s+\(RTK\.io\s+[→\-]+\s+Magnite[^)]*\)\.?', re.S),
        'Acquired exit as 1st technical hire (RTK.io → Magnite).',
    ),
    (
        re.compile(r'two\s+prior\s+exits\s+as\s+1st\s+engineer\s+\(RTK\.io\s+[→\-]+\s+Magnite[^)]*\)', re.S),
        'an acquired exit as 1st technical hire at RTK.io / Magnite',
    ),
    (
        re.compile(r'with\s+two\s+exits\)', re.S),
        'one acquired exit)',
    ),
    (
        re.compile(r'with\s+two\s+exits\b', re.S),
        'with an acquired exit',
    ),
    (
        re.compile(r'\b(?:Two|two)\s+prior\s+exits\b(?!\s*[\-—]\s+(?:RTK|RTK\.io))', re.S),
        'an acquired exit',
    ),
    (
        re.compile(r'\bTwo\s+exits\b', re.S),
        'Acquired exit at RTK.io / Magnite',
    ),
    (
        re.compile(r',\s*two\s+exits\)', re.S),
        ', one acquired exit)',
    ),
    (
        re.compile(r',\s+two\s+exits\.', re.S),
        ', with an acquired exit at RTK.io / Magnite.',
    ),
    (
        re.compile(r'others,\s+two\s+exits\)', re.S),
        'others, with an acquired exit)',
    ),
    # Bare parenthetical: "(two exits)" or "— two exits)" anywhere
    (
        re.compile(r'\(two\s+exits\)', re.S),
        '(an acquired exit at RTK.io / Magnite)',
    ),
    (
        re.compile(r'[—\-]\s*two\s+exits\)', re.S),
        '— acquired exit)',
    ),
    # "Magnite (10k+ users, exit)" — keep this alone.
]


# ---- per-application scrubs ----------------------------------------------------------

PER_APP = {
    "cerrion_full-stack-engineer": [
        # Drop the "Recent AI/ML work has been LLM-focused rather than CV..." sentence in summary.
        (
            re.compile(
                r' Recent AI/ML work has been LLM- and embedding-focused rather than computer vision, '
                r'but the surrounding production stack — TypeScript and Python web applications, real-time pipelines, '
                r'observability, scalable Postgres — is exactly what Cerrion\'s manufacturing product runs on\.'
            ),
            '',
        ),
    ],

    "mks-pamp_senior-full-stack-developer": [
        # Drop "Note: my primary backend is Python / Node.js / TypeScript, not Java — see cover letter for honest framing."
        (
            re.compile(
                r' Note: my primary backend is\s+Python / Node\.js / TypeScript, not Java [—\-]+ '
                r'see cover letter for honest framing\.'
            ),
            '',
        ),
    ],

    "stellium_cloud-and-ai-lead-nyon": [
        # Drop the upfront French / Power Platform / cert acknowledgments in summary.
        (
            re.compile(
                r' Open to certifications\s*'
                r'\(AZ-305 / AI-102\) on a clear plan\. French at B1\+ Professional Working [—\-]+ see\s*'
                r'cover letter for honest framing on the bilingual French / English\s*'
                r'requirement\. Power Platform \(Power Apps / Power Automate / Dataverse\) is\s*'
                r'the one stack-piece I\'d be ramping on\.'
            ),
            '',
        ),
    ],

    "corintis_full-stack-engineer": [
        # Restore education to clean "B.Sc., Criminal Justice / Economics" (no Master's apology).
        (
            re.compile(
                r'degree:\s*"B\.Sc\.\s*\(12\+ yrs senior industry experience compensates for the '
                r'Master\'s-preferred ask in the JD\)"'
            ),
            'degree: "B.Sc., Criminal Justice / Economics"',
        ),
    ],

    "rjc-group_software-developer-geneva-fs": [
        # Clean education entry — drop the ETH/EPFL/IP-Paris apology from the degree line.
        (
            re.compile(
                r'degree:\s*"B\.Sc\. [—\-]+ note:[^"]+"'
            ),
            'degree: "B.Sc., Criminal Justice / Economics"',
        ),
        # Clean EPFL role suffix.
        (
            re.compile(r'role:\s*"Software Engineer \(worked at EPFL, not an EPFL alumnus\)"'),
            'role: "Software Engineer"',
        ),
        # Pull "Note on degree:" sentence out of summary.
        (
            re.compile(
                r' Note on degree: my BSc is from\s*'
                r'Northeastern \(Boston\), with three years at the University of Exeter \(UK\) and\s*'
                r'the Metis Data Science Immersive \(NYC\)\. I worked at EPFL but am not an EPFL\s*'
                r'alumnus [—\-]+ see cover letter for honest framing\.'
            ),
            '',
        ),
    ],

    "google_software-engineer-youtube-shopping": [
        # Soften the level-mismatch self-flag in the summary (keep in cover letter).
        (
            re.compile(
                r' Note on level: this role is posted as Software Engineer II \(L4\);\s*'
                r'given my background I\'d be a stronger fit at L5 \(Senior\) or L6 \(Staff\) and\s*'
                r'would welcome Google considering my application at the appropriate level\. Happy\s*'
                r'to design and build at whichever level the team needs\.'
            ),
            '',
        ),
        (
            re.compile(
                r' Note on level: this role is posted as Software Engineer II \(L4\);\s*'
                r'given my background I\'d be a stronger fit at L5 \(Senior\) or L6 \(Staff\) and\s*'
                r'would welcome consideration at the appropriate level\.'
            ),
            '',
        ),
    ],
}


def scrub(slug: str, text: str) -> tuple[str, int]:
    n = 0
    for pat, repl in UNIVERSAL:
        new, k = pat.subn(repl, text)
        if k:
            n += k
            text = new
    for pat, repl in PER_APP.get(slug, []):
        new, k = pat.subn(repl, text)
        if k:
            n += k
            text = new
    return text, n


def main():
    changed = 0
    total_subs = 0
    for app_dir in sorted(APPS.iterdir()):
        if not app_dir.is_dir():
            continue
        path = app_dir / "tailored.yaml"
        if not path.exists():
            continue
        slug = app_dir.name.split("_", 1)[1]  # drop the date prefix
        text = path.read_text()
        new, n = scrub(slug, text)
        if n:
            path.write_text(new)
            print(f"  + {app_dir.name}: {n} edits")
            changed += 1
            total_subs += n
        else:
            print(f"  · {app_dir.name}: no changes")
    print(f"\nupdated {changed} files, {total_subs} total substitutions")


if __name__ == "__main__":
    main()
