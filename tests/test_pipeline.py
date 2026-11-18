import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402
import new_application  # noqa: E402
import render  # noqa: E402
import review  # noqa: E402
import score  # noqa: E402
import synthesize_achievements as synth  # noqa: E402


class MetricEmphasisTests(unittest.TestCase):
    def test_currency_multipliers_plus_and_ranges(self) -> None:
        cases = {
            "raised €4.4M seed": "raised <strong>€4.4M</strong> seed",
            "over $50M+ ad-tech": "over <strong>$50M+</strong> ad-tech",
            "3,370× faster": "<strong>3,370×</strong> faster",
            "10x and 10× speedups": "<strong>10x</strong> and <strong>10×</strong> speedups",
            "320+ PRs, 10k+ users, 1M+ nodes": (
                "<strong>320+</strong> PRs, <strong>10k+</strong> users, <strong>1M+</strong> nodes"
            ),
            "5% to 85% coverage": "<strong>5%</strong> to <strong>85%</strong> coverage",
            "on 162,000 rows": "on <strong>162,000</strong> rows",
        }
        for raw, expected in cases.items():
            got = str(render.metric_emphasis(raw))
            self.assertEqual(got, expected, raw)
            self.assertNotIn("<strong><strong>", got)

    def test_html_escaped_before_bolding(self) -> None:
        got = str(render.metric_emphasis("<script>alert('10x')</script> & 50%"))
        self.assertIn("&lt;script&gt;", got)
        self.assertIn("<strong>10x</strong>", got)
        self.assertIn("<strong>50%</strong>", got)
        self.assertNotIn("<script>", got)


class ClaimTokenTests(unittest.TestCase):
    def test_glued_units_typography_and_year_filtering(self) -> None:
        cases = {
            "raised €9.9M seed": {"9.9m"},
            "10x faster": {"10x"},
            "50k users": {"50k"},
            "from 25s to 7ms": {"25s", "7ms"},
            "3,370× faster": {"3,370x"},
            "3,370x faster": {"3,370x"},
            "on 162,000, rows": {"162,000"},
            "320+ merged PRs": {"320+"},
            "in 2019 and 12 months": set(),
        }
        for text, want in cases.items():
            self.assertEqual(review._claim_tokens(text), want, text)

    def test_existing_applications_have_zero_untraceable_claims(self) -> None:
        apps_dir = ROOT / "applications"
        if not apps_dir.exists():
            return
        corpus_tokens = review._claim_tokens(review._corpus())
        for app_dir in sorted(apps_dir.iterdir()):
            tp = app_dir / "tailored.yaml"
            if not tp.exists():
                continue
            t = yaml.safe_load(tp.read_text())
            claim_source = {k: v for k, v in t.items() if k not in ("meta", "cover_letter")}
            letter = t.get("cover_letter") or {}
            claim_source["cover_letter"] = [letter.get(k) for k in ("opening", "body", "closing")]
            claims = review._claim_tokens("\n".join(review._strings(claim_source)))
            self.assertEqual(sorted(claims - corpus_tokens), [], app_dir.name)


class ScoreTests(unittest.TestCase):
    def test_tokens_bigrams_and_whole_word_matching(self) -> None:
        self.assertEqual(
            score._tokens("You'll build Jua's K8s EC2 S3 GPT-4 stack"),
            ["build", "jua", "k8s", "ec2", "s3", "gpt-4", "stack"],
        )
        self.assertFalse(score._has_keyword("field", "shipped a greenfield service"))
        self.assertFalse(score._has_keyword("java", "typescript and javascript"))
        self.assertTrue(score._has_keyword("agent", "tool-calling agents"))
        self.assertTrue(score._has_keyword("retrieval", "indexing, retrieval and reranking"))
        self.assertTrue(score._has_keyword("design", "designed the data layer"))
        self.assertTrue(score._has_keyword("define", "defined standards"))

        kws = dict(score._extract_keywords("hybrid retrieval, reranking. hybrid retrieval, reranking."))
        self.assertNotIn("retrieval reranking", kws)
        self.assertEqual(kws.get("hybrid retrieval"), 2)


class ScaffoldAndReviewTests(unittest.TestCase):
    def test_scaffold_parses_profile_and_renders_cv_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = new_application.scaffold("Acme Corp", "AI Engineer", app_date="2026-11-18", out_root=Path(tmp))
            data = yaml.safe_load((app_dir / "tailored.yaml").read_text())
            self.assertTrue(data["basics"].get("location"))
            self.assertNotIn("title_variants", data["basics"])
            self.assertNotIn("summaries", data)
            self.assertNotIn("value_proposition", data)
            self.assertIsInstance(data["skills"], list)

            data["headline"] = "Senior AI Engineer"
            data["summary"] = "Delivered 243 merged PRs and 3,370x vector speedup."
            data["competencies"] = ["Agentic Systems", "MCP"]
            data["experience"] = render._normalise_experience(data["experience"])
            html_out = render._jinja("cv.html.j2").render(
                basics=data["basics"],
                headline=data["headline"],
                summary=data["summary"],
                competencies=data["competencies"],
                experience=data["experience"],
                skills=data["skills"],
                education=data["education"],
                languages=data["languages"],
                projects=data["projects"],
                key_achievements=[a["text"] for a in data["key_achievements"]],
            )
            self.assertIn("Core Competencies", html_out)
            self.assertIn("https://github.com/smitfire", html_out)

    def test_review_flags_cover_letter_prose_and_white_text_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "2026-11-18_acme_ai"
            app_dir.mkdir()
            (app_dir / "jd.md").write_text("python fastapi mcp python fastapi mcp")
            (app_dir / "cv.html").write_text(
                "<html><style>body{background:#fff8f0;color:#111;}</style><body>ok</body></html>"
            )
            for fn in ("cv.pdf", "cv.docx", "cover_letter.pdf"):
                (app_dir / fn).write_bytes(b"%PDF-1.4\n")
            tailored = {
                "meta": {"company": "Acme", "role_title": "AI Engineer", "jd_keywords": ["a"] * 10},
                "headline": "AI Engineer",
                "summary": "Python FastAPI MCP engineer.",
                "experience": [],
                "skills": [],
                "education": [],
                "languages": [],
                "cover_letter": {
                    "company": "Acme",
                    "role_title": "AI Engineer",
                    "opening": "Hello Acme AI team.",
                    "body": "TODO fix this 999% speedup claim before sending.",
                    "closing": "Thanks.",
                },
            }
            (app_dir / "tailored.yaml").write_text(yaml.safe_dump(tailored, sort_keys=False))
            cv_text = " ".join(["python fastapi mcp"] * 200)
            with (
                mock.patch.object(score, "_read_cv_text", return_value=cv_text),
                mock.patch.object(review, "_pdf_text", return_value="Acme AI " + "word " * 180),
                mock.patch.object(review, "_pdf_meta", return_value={"/Title": "T", "/Author": "Nick", "/Keywords": "k" * 25}),
            ):
                rc = review.review(app_dir)
            self.assertEqual(rc, 1)
            report = (app_dir / "review.md").read_text()
            self.assertIn("placeholders found: TODO", report)
            self.assertIn("`999%`", report)
            self.assertIn("| ATS: single column, no hidden text | PASS |", report)

            (app_dir / "cv.html").write_text("<html><style>.hide{color: #fff;}</style></html>")
            with (
                mock.patch.object(score, "_read_cv_text", return_value=cv_text),
                mock.patch.object(review, "_pdf_text", return_value="Acme AI " + "word " * 180),
                mock.patch.object(review, "_pdf_meta", return_value={"/Title": "T", "/Author": "Nick", "/Keywords": "k" * 25}),
            ):
                rc2 = review.review(app_dir)
            self.assertEqual(rc2, 1)
            self.assertIn("ATS flags in cv.html: color:#fff", (app_dir / "review.md").read_text())


class SiteAndHygieneTests(unittest.TestCase):
    def test_dates_meta_desc_and_site_up_to_date(self) -> None:
        self.assertEqual(build_site.fmt_period({"start": "2026-08", "end": "present"}), "Aug 2026 — Present")
        desc = build_site._meta_desc("alpha beta gamma delta epsilon zeta eta", limit=20)
        self.assertLessEqual(len(desc), 20)
        self.assertEqual(desc, "alpha beta gamma…")

        profile = yaml.safe_load((ROOT / "source" / "profile.yaml").read_text())
        self.assertEqual((ROOT / "docs" / "index.html").read_text(), build_site.render(profile))

    def test_public_files_pass_nda_and_style_sanitization(self) -> None:
        banned = re.compile(
            r"TWAP-|NMI-|OPS-|NDB-|NatzkaLabs|Delta-Labs-AG|Ranova-AI|LessSimpleDSS|"
            r"vit-natzka|stefandejong|carmaycur|skivanachanrion|eplightning|"
            r"laureat-natzka|justinas-natzka|nertil-natzka|Vitalii|DietrichGebert|"
            r"ponytail|career-ops|ai_notes_min",
            re.I,
        )
        for rel in ("source/profile.yaml", "source/achievements_public.yaml", "source/positioning.md", "docs/index.html"):
            txt = (ROOT / rel).read_text()
            self.assertEqual(banned.findall(txt), [], rel)

        pos_txt = (ROOT / "source" / "positioning.md").read_text()
        self.assertNotIn("—", pos_txt)
        self.assertNotIn("–", pos_txt)

        profile = yaml.safe_load((ROOT / "source" / "profile.yaml").read_text())
        vp = profile.get("value_proposition") or {}
        for text in [vp.get("headline", "")] + [p["blurb"] for p in vp.get("pillars", [])]:
            self.assertNotIn("—", text)
            self.assertNotIn("–", text)
        for k, s in (profile.get("summaries") or {}).items():
            self.assertNotIn("—", s, k)
            self.assertNotIn("–", s, k)
        natzka_role = next(e for e in profile["experience"] if e["id"] == "natzka")
        for b in natzka_role["bullets"]:
            self.assertNotIn("—", b["text"])
            self.assertNotIn("–", b["text"])


class SynthesizeTests(unittest.TestCase):
    def test_discovers_prefixed_harvest_files_and_dict_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp)
            (raw / "sample_prs_full.json").write_text(
                json.dumps([
                    {
                        "number": 1,
                        "title": "feat: add caching",
                        "body": "2x faster response",
                        "repository": {"nameWithOwner": "org/app"},
                        "additions": 10,
                        "deletions": 2,
                        "changedFiles": 1,
                        "mergedAt": "2026-11-18T10:00:00Z",
                        "labels": [{"name": "perf"}],
                    },
                    {
                        "number": 2,
                        "title": "migrate service",
                        "body": "",
                        "repository": "org/other",
                        "additions": 5,
                        "deletions": 1,
                        "changedFiles": 1,
                        "mergedAt": "2026-11-18T11:00:00Z",
                        "labels": {"nodes": [{"name": "infra"}]},
                    },
                ])
            )
            (raw / "sample_jira_done.json").write_text(json.dumps({"issues": [], "isLast": True}))
            synth.main(raw)
            digest = yaml.safe_load((raw / "digest.yaml").read_text())
            self.assertEqual(digest["summary"]["github_prs"], 2)
            self.assertEqual(digest["summary"]["jira_done"], 0)
            self.assertIn("org/app", digest["summary"]["by_repo_prs"])
            self.assertIn("sample", (raw / "highlights.md").read_text())


if __name__ == "__main__":
    unittest.main()
