#!/usr/bin/env python3
"""
Read raw GitHub PRs + Jira tickets + git logs from source/raw_harvest/, classify
each item along the three axes (perf / feature / transition), extract quantitative
signals, and emit a structured digest.

Usage:
    python scripts/synthesize_achievements.py
    # writes:
    #   source/raw_harvest/digest.yaml          (full categorized digest)
    #   source/raw_harvest/highlights.md        (human-skimmable, top items per axis)
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "source" / "raw_harvest"

# ---- axis classifiers (regex over title + body, lowercase) ------------------

PERF_PAT = re.compile(
    r"\b(perf|performance|optim|optimi[sz]ation|speed[- ]?up|latency|cache|"
    r"caching|index(?:ing)?|slow|n\+1|throughput|p9[59]|response time|"
    r"reduce time|faster|memo[i]?z|debounce|throttle|batch|batching|"
    r"lazy[- ]?load|preload|streaming|eagerload|background job|inngest)\b",
    re.I,
)
FEATURE_PAT = re.compile(
    r"\b(feat|feature|launch|ship|introduce|add(?:s)? .* (?:support|ability|page|"
    r"endpoint|view|component|dashboard|export|report|generation|integration)|"
    r"new (?:page|view|component|dashboard|endpoint|feature|module)|implement|"
    r"build out|user[- ]facing|client[- ]facing|MVP|GA)\b",
    re.I,
)
TRANSITION_PAT = re.compile(
    r"\b(migrat\w*|upgrade|refactor|rewrite|replace|switch (?:to|from)|"
    r"transition|introduce \w+ (?:framework|library|tool|service)|"
    r"set up new|new pipeline|new infrastructure|move to|move from|"
    r"deprecat|sunset|architectural|sdk migration)\b",
    re.I,
)
RELEASE_PAT = re.compile(r"^\s*(release|chore\(release\))[:\s]", re.I)

# Patterns that extract numeric impact signals from bodies.
METRIC_PATTERNS = [
    re.compile(r"(\d+(?:\.\d+)?)\s*x\s*(?:faster|speed[- ]?up|throughput|less|reduction)", re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s*%\s*(?:faster|slower|reduction|reduced|improvement|less|more|fewer)", re.I),
    re.compile(r"(?:from|was)\s+(\d+(?:\.\d+)?)\s*(?:ms|s|seconds|minutes?|hours?)\s+(?:to|down to)\s+(\d+(?:\.\d+)?)\s*(ms|s|seconds|minutes?|hours?)", re.I),
    re.compile(r"\bp(?:95|99|50)\s*[:\s]+\d+(?:\.\d+)?\s*(?:ms|s)", re.I),
    re.compile(r"\$\s*\d[\d,]*\s*(?:saved|reduction|less)", re.I),
    re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:ms|s|seconds|minutes?|hours?)\b", re.I),
    re.compile(r"\b(?:coverage|throughput|latency|recall|precision)\s*[:\s]+\d+(?:\.\d+)?", re.I),
]


def classify(text: str) -> list[str]:
    axes = []
    if RELEASE_PAT.search(text):
        return ["release"]  # release PRs handled separately
    if PERF_PAT.search(text):
        axes.append("perf")
    if TRANSITION_PAT.search(text):
        axes.append("transition")
    if FEATURE_PAT.search(text):
        axes.append("feature")
    return axes or ["other"]


def extract_metrics(text: str) -> list[str]:
    if not text:
        return []
    found = set()
    for pat in METRIC_PATTERNS:
        for m in pat.finditer(text):
            found.add(m.group(0).strip())
    return sorted(found)


# ---- ADF (Atlassian doc format) flattening ----------------------------------


def flatten_adf(node) -> str:
    if not node:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(flatten_adf(n) for n in node)
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    return flatten_adf(node.get("content", []))


# ---- ingest ----------------------------------------------------------------


def load_prs() -> list[dict]:
    prs = json.load(open(RAW / "github_prs_full.json"))
    out = []
    for p in prs:
        title = p.get("title") or ""
        body = p.get("body") or ""
        text = f"{title}\n{body}"
        axes = classify(text)
        out.append({
            "kind": "pr",
            "id": f"{p['repository']}#{p['number']}",
            "repo": p["repository"],
            "title": title,
            "url": p.get("url"),
            "additions": p.get("additions", 0),
            "deletions": p.get("deletions", 0),
            "files": p.get("changedFiles", 0),
            "merged_at": (p.get("mergedAt") or "")[:10],
            "labels": [l["name"] for l in p.get("labels", {}).get("nodes", [])],
            "axes": axes,
            "metrics": extract_metrics(body),
            "body_excerpt": (body[:600] + "…") if len(body) > 600 else body,
        })
    return out


def load_jira() -> list[dict]:
    issues = json.load(open(RAW / "jira_done_full.json"))
    out = []
    for i in issues:
        f = i["fields"]
        desc = flatten_adf(f.get("description"))
        title = f.get("summary") or ""
        text = f"{title}\n{desc}"
        axes = classify(text)
        out.append({
            "kind": "jira",
            "id": i["key"],
            "project": f["project"]["key"],
            "type": f["issuetype"]["name"],
            "title": title,
            "resolved": (f.get("resolutiondate") or "")[:10],
            "labels": f.get("labels", []),
            "components": [c["name"] for c in (f.get("components") or [])],
            "axes": axes,
            "metrics": extract_metrics(desc),
            "desc_excerpt": (desc[:400] + "…") if len(desc) > 400 else desc,
        })
    return out


GIT_COMMIT_RE = re.compile(r"^([0-9a-f]{7,})\|(\d{4}-\d{2}-\d{2})\|(.+)$")


def load_git_logs() -> list[dict]:
    out = []
    for f in sorted((RAW / "git_logs").glob("*.log")):
        repo = f.stem
        text = f.read_text()
        # parse: each commit is "<sha>|<date>|<subj>\n<stat-line maybe blank>\n"
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            m = GIT_COMMIT_RE.match(lines[i])
            if not m:
                i += 1
                continue
            sha, date, subj = m.groups()
            stat_line = ""
            j = i + 1
            while j < len(lines) and (lines[j].startswith(" ") or "files changed" in lines[j]):
                if "files changed" in lines[j] or "insertion" in lines[j] or "deletion" in lines[j]:
                    stat_line = lines[j].strip()
                    break
                j += 1
            insertions = deletions = 0
            stm = re.search(r"(\d+) insertion", stat_line)
            if stm: insertions = int(stm.group(1))
            stm = re.search(r"(\d+) deletion", stat_line)
            if stm: deletions = int(stm.group(1))
            axes = classify(subj)
            out.append({
                "kind": "commit",
                "id": f"{repo}@{sha}",
                "repo": repo,
                "title": subj,
                "date": date,
                "insertions": insertions,
                "deletions": deletions,
                "axes": axes,
            })
            i = j + 1
    return out


# ---- digest ----------------------------------------------------------------


def main():
    prs = load_prs()
    jira = load_jira()
    commits = load_git_logs()

    by_axis = defaultdict(list)
    for item in prs + jira + commits:
        for a in item["axes"]:
            by_axis[a].append(item)

    # rank PRs by additions, jira by recency, commits by insertions
    def rank(items):
        prs   = sorted([i for i in items if i["kind"] == "pr"],     key=lambda x: -x["additions"])
        ji    = sorted([i for i in items if i["kind"] == "jira"],   key=lambda x: x.get("resolved",""), reverse=True)
        cmts  = sorted([i for i in items if i["kind"] == "commit"], key=lambda x: -x.get("insertions",0))
        return prs, ji, cmts

    digest = {"summary": {}, "perf": {}, "feature": {}, "transition": {}, "release": {}, "other": {}}
    digest["summary"] = {
        "github_prs": len(prs),
        "jira_done": len(jira),
        "commits": len(commits),
        "by_axis": {a: len(by_axis[a]) for a in ("perf","feature","transition","release","other")},
        "by_repo_prs": {},
        "by_repo_commits": {},
    }
    from collections import Counter
    digest["summary"]["by_repo_prs"] = dict(Counter(p["repo"] for p in prs).most_common())
    digest["summary"]["by_repo_commits"] = dict(Counter(c["repo"] for c in commits).most_common())

    for axis in ("perf","feature","transition","release","other"):
        prs_a, ji_a, cmts_a = rank(by_axis[axis])
        digest[axis] = {
            "prs": prs_a[:50],
            "jira": ji_a[:50],
            "commits": cmts_a[:30],
        }

    (RAW / "digest.yaml").write_text(yaml.safe_dump(digest, sort_keys=False, allow_unicode=True, width=120))
    print(f"wrote {RAW / 'digest.yaml'}")

    # Human highlights — top of each axis
    md = ["# Achievements digest — Delta Labs (org-wide)\n",
          f"Generated from `source/raw_harvest/`. Source totals: {digest['summary']['github_prs']} merged PRs, "
          f"{digest['summary']['jira_done']} done Jira tickets, {digest['summary']['commits']} local commits.\n",
          "## Distribution\n"]
    for k, v in digest["summary"]["by_axis"].items():
        md.append(f"- **{k}**: {v} items")
    md.append("\n## By repo (PRs)\n")
    for k, v in digest["summary"]["by_repo_prs"].items():
        md.append(f"- `{k}`: {v} PRs")

    for axis in ("perf","feature","transition"):
        md.append(f"\n## Top — {axis}\n")
        sec = digest[axis]
        if sec["prs"]:
            md.append("### GitHub PRs (by LOC)\n")
            for p in sec["prs"][:15]:
                line = f"- **`{p['repo']}#{p['id'].split('#')[-1]}`** (+{p['additions']:,}/-{p['deletions']:,}, {p['files']} files) — {p['title']}"
                if p['metrics']:
                    line += f"\n  - metrics: {', '.join(p['metrics'][:3])}"
                md.append(line)
        if sec["jira"]:
            md.append("\n### Jira (most recent)\n")
            for i in sec["jira"][:15]:
                line = f"- **{i['id']}** [{i['type']}] ({i['resolved']}) — {i['title']}"
                if i['metrics']:
                    line += f"\n  - metrics: {', '.join(i['metrics'][:3])}"
                md.append(line)
        if sec["commits"]:
            md.append("\n### Commits (largest)\n")
            for c in sec["commits"][:10]:
                md.append(f"- **`{c['id']}`** (+{c['insertions']}/-{c['deletions']}) — {c['title']}")

    (RAW / "highlights.md").write_text("\n".join(md))
    print(f"wrote {RAW / 'highlights.md'}")
    print(f"\nsummary:")
    for k, v in digest["summary"]["by_axis"].items():
        print(f"  {k:12} {v:>4}")


if __name__ == "__main__":
    main()
