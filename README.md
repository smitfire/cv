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
  review.py                 # validation cycle → review.md (checks + critical rubric)
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

# 3. render (runs the validation pass automatically; --skip-review to opt out)
python scripts/render.py applications/<slug>/

# 4. score (standalone; same keyword metric review.py uses)
python scripts/score.py applications/<slug>/

# 5. re-run the validation pass any time
python scripts/review.py applications/<slug>/
```

Target ≥ 70-80% keyword match. Below 60% means the CV needs more JD-aligned wording.

## Validation cycle

`render.py` writes `review.md` next to the CV. The pass has two halves:

**Automated checks** (deterministic, must pass):
- required files, JD metadata (`meta.company / role_title / jd_keywords`), no placeholders
- keyword match against `jd.md` (hard floor 60%, target 70%+)
- claim traceability: every distinctive numeric claim in `tailored.yaml` must exist in `source/profile.yaml` or `source/achievements_public.yaml` (catches invented or mistyped metrics)
- timeline sanity: start/end order, a single "present" role, overlap warnings
- ATS safety: no tables, hidden text, white-on-white, or zero-size fonts in `cv.html`
- PDF metadata present; CV and cover-letter length sanity
- style: no em/en dashes in authored text (templates keep their separators)

**Critical review** (judgement, complete in `review.md` before sending): positioning, JD coverage in the JD's own vocabulary, evidence quality, gaps and risks, cover-letter specificity, and a final `SHIP` / `REVISE` verdict. Treat it as a red-team pass: the goal is to find the reason a recruiter would say no.

Exit code is non-zero when a hard check fails, so the cycle can gate a send.

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
