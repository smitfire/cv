#!/usr/bin/env python3
"""
build_site.py — Generate the public CV website at docs/index.html from profile.yaml.

Run:
    python scripts/build_site.py

Outputs a single self-contained docs/index.html with embedded CSS — no external
dependencies, no JS frameworks, GitHub-Pages-ready.
"""
from __future__ import annotations

import html
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "source" / "profile.yaml"
OUT = ROOT / "docs" / "index.html"

# Pick which experiences to feature (most recent / most relevant first).
FEATURED_EXP_IDS = ["delta_labs", "ranova", "epfl", "rtkio"]

# Pick which skill categories to surface (in order — AI first, leadership-relevant second).
FEATURED_SKILLS = ["ai_llm", "python", "frontend", "data", "cloud_devops", "observability"]

# Pick which projects to highlight — AI-first.
FEATURED_PROJECTS = [
    "RAG / Semantic Search Platform (Delta Labs)",
    "Recursive Language Models (RLM) Inference Service (Delta Labs)",
    "AI Agent Skills + MCP Framework (Delta Labs)",
    "Document Extract / OCR Microservice (Delta Labs)",
]

# Default summary + headline pick — leads on AI / LLM (current focus) + leadership signal.
DEFAULT_HEADLINE = "Senior AI / Full Stack Engineer · RAG · RLM · Agentic AI"
DEFAULT_SUMMARY_KEY = "ai_engineer"


# --- helpers ----------------------------------------------------------------


def fmt_date(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, int):
        return str(v)
    if isinstance(v, (date,)):
        return v.strftime("%b %Y")
    return str(v)


def fmt_period(role: dict) -> str:
    s = fmt_date(role.get("start"))
    e = role.get("end")
    e_str = "Present" if e in (None, "present", "Present") else fmt_date(e)
    return f"{s} — {e_str}"


def esc(s: str) -> str:
    return html.escape(str(s)) if s is not None else ""


# --- render -----------------------------------------------------------------


def render(profile: dict) -> str:
    basics = profile["basics"]
    summary = profile["summaries"][DEFAULT_SUMMARY_KEY].strip()

    exp_by_id = {e["id"]: e for e in profile["experience"]}
    experiences = [exp_by_id[i] for i in FEATURED_EXP_IDS if i in exp_by_id]

    skills_data = profile["skills"]
    skills = [skills_data[k] for k in FEATURED_SKILLS if k in skills_data]

    projects_by_title = {p["title"]: p for p in profile.get("projects", [])}
    projects = [projects_by_title[t] for t in FEATURED_PROJECTS if t in projects_by_title]

    education = profile.get("education", [])
    languages = profile.get("languages", [])
    achievements = profile.get("key_achievements", [])

    # ---- HTML ----
    out = []
    out.append(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(basics['name'])} — {esc(DEFAULT_HEADLINE)}</title>
<meta name="description" content="{esc(' '.join(summary.split())[:160])}">
<meta name="author" content="{esc(basics['name'])}">
<meta property="og:title" content="{esc(basics['name'])} — {esc(DEFAULT_HEADLINE)}">
<meta property="og:description" content="{esc(' '.join(summary.split())[:160])}">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="grain" aria-hidden="true"></div>
<main class="page">

  <header class="hero">
    <div class="hero__top">
      <div class="hero__id">
        <h1>{esc(basics['name'])}</h1>
        <p class="hero__role">{esc(DEFAULT_HEADLINE)}</p>
      </div>
      <button class="theme-toggle" aria-label="Toggle theme" type="button">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"></path>
        </svg>
      </button>
    </div>
    <ul class="hero__contact">
      <li>{esc(basics['location'])}</li>
      <li><a href="mailto:{esc(basics['email'])}">{esc(basics['email'])}</a></li>
      <li><a href="{esc(basics['linkedin'])}" rel="me">LinkedIn</a></li>""")

    if basics.get("sites", {}).get("personal"):
        site = basics["sites"]["personal"]
        out.append(f'      <li><a href="{esc(site)}">{esc(site.replace("https://", ""))}</a></li>')

    out.append("""    </ul>
  </header>

  <section class="brief">
    <p>""" + esc(" ".join(summary.split())) + """</p>
  </section>
""")

    # Experience
    out.append('  <section class="experience">')
    out.append('    <h2 class="section-title">Experience</h2>')
    out.append('    <ol class="timeline">')
    for r in experiences:
        period = fmt_period(r)
        loc = r.get("location", "")
        blurb = r.get("blurb", "").strip()
        bullets = r.get("bullets", [])[:5]
        stack = r.get("stack", [])
        out.append(f"""      <li class="role">
        <header class="role__header">
          <div class="role__title">
            <h3>{esc(r['role'])}</h3>
            <p class="role__company">{esc(r['company'])}{f' · <span class="role__loc">{esc(loc)}</span>' if loc else ''}</p>
          </div>
          <time class="role__period">{esc(period)}</time>
        </header>""")
        if blurb:
            out.append(f'        <p class="role__blurb">{esc(blurb)}</p>')
        if bullets:
            out.append('        <ul class="role__bullets">')
            for b in bullets:
                # b can be a dict (with text+tags) or a string
                text = b["text"] if isinstance(b, dict) else b
                out.append(f"          <li>{esc(text)}</li>")
            out.append("        </ul>")
        if stack:
            out.append('        <ul class="stack">')
            for tech in stack:
                out.append(f'          <li>{esc(tech)}</li>')
            out.append("        </ul>")
        out.append("      </li>")
    out.append("    </ol>")
    out.append("  </section>\n")

    # Selected achievements (compact callout grid)
    if achievements:
        out.append('  <section class="callouts">')
        out.append('    <h2 class="section-title">Selected wins</h2>')
        out.append('    <ul class="callouts__grid">')
        for a in achievements[:6]:
            text = a["text"] if isinstance(a, dict) else a
            out.append(f'      <li>{esc(text)}</li>')
        out.append('    </ul>')
        out.append('  </section>\n')

    # Projects
    if projects:
        out.append('  <section class="projects">')
        out.append('    <h2 class="section-title">Selected projects</h2>')
        out.append('    <ul class="projects__grid">')
        for p in projects:
            out.append(f"""      <li class="project">
        <h3>{esc(p['title'])}</h3>
        <p>{esc(p['blurb'])}</p>
      </li>""")
        out.append('    </ul>')
        out.append('  </section>\n')

    # Skills
    out.append('  <section class="skills">')
    out.append('    <h2 class="section-title">Skills</h2>')
    out.append('    <dl class="skills__list">')
    for s in skills:
        items = ", ".join(s["items"])
        out.append(f"""      <div class="skills__row">
        <dt>{esc(s['label'])}</dt>
        <dd>{esc(items)}</dd>
      </div>""")
    out.append('    </dl>')
    out.append('  </section>\n')

    # Education + Languages (two-up)
    out.append('  <section class="meta">')
    out.append('    <div class="meta__col">')
    out.append('      <h2 class="section-title">Education</h2>')
    out.append('      <ul class="edu">')
    for e in education[:4]:
        loc = f", {e['location']}" if e.get("location") else ""
        end = f" – {e['end']}" if e.get("end") else ""
        out.append(f"""        <li>
          <strong>{esc(e['school'])}</strong>
          <span>{esc(e['degree'])}{esc(loc)}</span>
          <time>{esc(e['start'])}{esc(end)}</time>
        </li>""")
    out.append('      </ul>')
    out.append('    </div>')

    out.append('    <div class="meta__col">')
    out.append('      <h2 class="section-title">Languages</h2>')
    out.append('      <ul class="languages">')
    for l in languages:
        out.append(f"        <li><strong>{esc(l['name'])}</strong> <span>{esc(l['level'])}</span></li>")
    out.append('      </ul>')
    out.append('    </div>')
    out.append('  </section>\n')

    # Footer
    out.append(f"""  <footer class="page__footer">
    <p>Reach me at <a href="mailto:{esc(basics['email'])}">{esc(basics['email'])}</a> or via <a href="{esc(basics['linkedin'])}">LinkedIn</a>.</p>
    <p class="page__footer-meta">
      <span>Last updated {date.today().strftime('%B %Y')}</span>
      <span aria-hidden="true">·</span>
      <a href="?print=1" onclick="window.print();return false;">Print / save as PDF</a>
    </p>
  </footer>

</main>

<script>
(function() {{
  const KEY = 'theme';
  const root = document.documentElement;
  const saved = localStorage.getItem(KEY);
  if (saved === 'dark' || saved === 'light') root.dataset.theme = saved;
  document.querySelector('.theme-toggle').addEventListener('click', () => {{
    const cur = root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    localStorage.setItem(KEY, next);
  }});
}})();
</script>
</body>
</html>
""")

    return "\n".join(out)


def main() -> None:
    profile = yaml.safe_load(PROFILE.read_text())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(profile))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
