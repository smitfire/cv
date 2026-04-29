# Nick Smit — CV pipeline + portfolio site

A small, repeatable pipeline that takes one YAML source of truth and produces:

1. **Per-application tailored CVs** — PDF + DOCX + cover letter, ATS-safe single-column, with `/Title /Author /Subject /Keywords` metadata populated per job description.
2. **A public portfolio site** — typography-led, light/dark, print-friendly, deployed to GitHub Pages from `docs/`.

## Repo layout

```
source/
  profile.yaml              # SINGLE source of truth (career, skills, education)
  achievements_public.yaml  # sanitised achievement bank (no IP, no client names)
templates/
  cv.html.j2                # ATS-safe single-column → PDF
  cover_letter.md.j2        # markdown cover-letter template
scripts/
  build_site.py             # profile.yaml → docs/index.html
  new_application.py        # scaffold a dated applications/<slug>/ folder
  render.py                 # tailored.yaml → cv.pdf + cv.docx + cover_letter.pdf
  score.py                  # JD vs rendered-CV keyword match score
  synthesize_achievements.py  # raw GitHub PR / Jira / git-log data → curated digest
docs/                       # GitHub Pages source (index.html + styles.css)
requirements.txt
```

Items kept locally only (gitignored):

```
applications/               # active per-application folders (private)
archive/                    # older loose CV PDFs
source/achievements_bank.yaml   # full achievement bank (contains client / project names)
source/raw_harvest/         # raw GitHub PR + Jira ticket exports
.env                        # Jira API token + repo paths
.venv/
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# WeasyPrint needs Pango / Cairo on macOS:
brew install pango cairo gdk-pixbuf libffi
```

## Per-application workflow

```bash
# 1. scaffold
python scripts/new_application.py "Acme Corp" "Senior Python Engineer"

# 2. paste JD into applications/<date>_<co>_<role>/jd.md, then edit tailored.yaml
#    against the JD (a long-context LLM is good at this)

# 3. render
python scripts/render.py applications/<slug>/

# 4. score
python scripts/score.py applications/<slug>/
```

Target ≥ 70-80% keyword match. Below 60% means the CV needs more JD-aligned wording.

## Building the portfolio site

```bash
python scripts/build_site.py
# → writes docs/index.html

# Preview locally
python -m http.server 8000 --bind 127.0.0.1 --directory docs
# → open http://127.0.0.1:8000
```

GitHub Pages: in repo settings → Pages → source = `Deploy from a branch`, branch = `main`, folder = `/docs`. The site goes live at `https://<user>.github.io/<repo>/`.

## ATS strategy

**Yes:**
- Single-column, no tables / icons / skill-bars — the parser reads top-to-bottom cleanly.
- Natural keyword integration in body text — every keyword paired with a verb + outcome.
- PDF/DOCX metadata (`/Title /Author /Subject /Keywords`) populated per JD — visible in document properties, ~23% lift in recruiter-search visibility (Jobscan study).
- Both `.pdf` and `.docx` rendered; submit whichever the posting prefers.

**No:**
- White-fonted / 1pt / hidden keywords ("white fonting"). Modern ATS (HireVue, Eightfold, Workday) detect this; recruiters select-all and see it instantly. ManpowerGroup alone flags ~100 k resumes/year for it. Outcomes when caught: rejection, or a permanent "do not consider" flag on the candidate. The downside is asymmetric.

## Privacy / NDA

This repo is public. Anything that touches client names, internal repo names, internal Jira keys, or proprietary architecture details lives in gitignored files (`source/achievements_bank.yaml`, `source/raw_harvest/`, `applications/`, `.env`). The committed `source/achievements_public.yaml` is a sanitised superset — it keeps the metrics and patterns and tech stack, scrubs anything identifying.

## License

Code: MIT. Content (CV text in `source/profile.yaml`, the rendered site): personal — please don't copy verbatim.
