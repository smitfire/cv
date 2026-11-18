# Nick Smit: Positioning, Value Proposition & Profile Copy

Sanitized, copy-paste-ready positioning backed by `source/profile.yaml` and `source/achievements_public.yaml`. No NDA-protected client names, internal ticket keys, or private repository details.

---

## Core Positioning Thesis

> I turn ambiguous, high-risk AI product ideas into governed, measured production systems, and multiply the engineering team around them by encoding security, correctness, and verification into the harness itself.

### 30-Second Pitch

I am a senior full-stack and AI engineer with 12+ years building production systems from seed-stage startups to acquired exits and European research labs. Most recently at Natzka, I shipped our production AI Assistant, docked 7-screen Chat Panel, 11-tool OAuth MCP server with human-in-the-loop workflow approvals, a 275-check evaluation harness with LLM-as-judge grading, and a 15-PR IAM security remediation, while reviewing 54 teammate PRs and building an 11-agent / 21-skill Claude Code harness that cut review noise and test bloat. Before that I led AI and backend delivery at Delta Labs (EUR 4.4M seed, 3,370x pg_diskann speedup, 5% to 85% test coverage), served as CTO at Ranova, built EPFL Blue Brain's open-source 1M+ node knowledge-graph frontend, and was the first technical hire at RTK.io (acquired by Magnite).

---

## Five Value-Add Pillars

1. **Governed Production AI (Safety & Grounding by Construction)**
   Treat every LLM boundary as an untrusted distributed system: RFC 9728 OAuth MCP servers with audience-bound tokens, whitelist chat persistence that drops customer data by default, untrusted context isolated outside cached instructions, atomic human-in-the-loop approval cards for write tools, AWS Bedrock (EU) / EU-endpoint residency, per-tenant token budgets, and live figure-grounding checks.
2. **Empirical Rigor Over Vibes (Falsification & Cleanroom Evals)**
   Replace gut-feel QA and vendor claims with falsifiable evidence: a 275-check / 91-scored-case assistant eval suite (186 total cases) with 20 paired refusal traps, dual-pass Bedrock EU LLM-as-judge grading, and Playwright UI replay (after an audit exposed 61 unscored turns out of 100); paired cleanroom benchmarks in Forewisp (17,912 B to 0 B false-positive context, 30 to 34 solves, -23% wall time); a 21-cell live sandbox bypass matrix; and preregistered 5% optimization gates.
3. **Team-Wide Engineering Leverage (Harness, Review & Test Architecture)**
   Multiply team throughput while shipping at high individual velocity (272 PRs opened / 243 merged in 15 weeks at Natzka; 320+ merged PRs in 10 months at Delta Labs; 848 merged + 26 open PRs in personal R&D): distilled 662 review comments through 3 falsifying skeptic agents into 38 verified rules across 11 specialist agents and 21 skills, reviewed 54 teammate PRs (113 passes, 195 inline comments) with isolated worktree mutation controls, audited tests across 9 PRs (+891 / -3,065), and lifted Delta Labs test coverage from 5% to 85%.
4. **End-to-End Systems Depth (Database Internals to Interactive UX)**
   Own bottlenecks across the full stack: 3,370x PostgreSQL vector-search speedup (25s to 7ms on 162k rows via pg_diskann with zero app code change), overcoming Postgres's 256 MB JSONB limit, 2.7 GB+ streaming ETL imports, 40 to 70% serverless memory cuts, 300% ETL uplift and 40% AWS cost cut at Ranova, up to a 7-screen context-aware docked React chat and a 1M+ node neuroscience knowledge-graph UI at EPFL.
5. **Zero-to-One Ownership, Security Mindset & Clean Handover**
   Trusted technical anchor from seed to exit: 1st technical hire scaling RTK.io to 10k+ active users and acquisition by Magnite, CTO at Ranova, Team Lead through Delta Labs' EUR 4.4M seed round, and leading Natzka's AI Assistant, customer MCP rollout, 15-PR IAM security remediation, CI supply-chain hardening, candidate take-home assessments, and capability-gap handover roadmaps.

---

## LinkedIn Headlines (<= 220 chars)

**AI Platform / Staff AI Engineer:**
```text
Senior / Staff AI Engineer | Production Agents, OAuth MCP, RAG & LLM Evals | Python, TypeScript, Postgres | Ex-Team Lead (EUR 4.4M seed), CTO & 1st Hire (Acquired)
```

**Full-Stack AI Lead:**
```text
Senior Full-Stack AI Engineer | Turning High-Risk LLM Ideas into Governed, Measured Production Systems | TypeScript, React, Python, MCP, AWS/Azure | Geneva & Zurich
```

**Founding Engineer / Tech Lead:**
```text
Founding Engineer / Tech Lead | 0-to-1 AI Platforms, Security & Engineering Leverage | 1st Hire to Exit (RTK.io / Magnite), Ex-CTO (Ranova), Team Lead (Delta Labs)
```

---

## LinkedIn "About" Section (< 2,000 chars)

```text
I turn ambiguous, high-risk AI ideas into governed, measured production systems, and multiply the engineering team around them by encoding security, correctness, and verification into the tools we ship with.

Over 12+ years in Zurich and Geneva, I have built 0-to-1 AI and full-stack platforms where correctness, governance, and velocity all matter:

- Governed Production AI: Tool-calling assistants and RFC 9728 OAuth MCP servers with HITL write approvals, whitelist privacy persistence (zero customer data stored in chat), prompt-injection isolation, AWS Bedrock (EU) residency, per-tenant token budgets, and live figure grounding.
- Empirical Evaluation: 275-check / 91-scored-case assistant eval suite with paired refusal traps, Bedrock EU LLM-as-judge grading, and Playwright UI replay; Forewisp adaptive context engine backed by cleanroom multi-model benchmarks cutting false-positive context from 17,912 B to 0 B and wall time up to 23%.
- Engineering Leverage: Distilled 662 PR review comments via skeptic agents into 38 verified rules across 11 specialist agents and 21 progressive-disclosure skills; raised backend test coverage from 5% to 85% (100% on async workflows).
- Systems Depth (DB to UX): 3,370x Postgres vector speedup (25s to 7ms via pg_diskann), 2.7 GB+ streaming ETL ingestion, 300% ETL uplift, 40% AWS cost cut, a 7-screen docked React chat panel, and EPFL Blue Brain's open-source 1M+ node knowledge-graph UI.

Track record: Senior Software Engineer at Natzka (272 PRs opened / 243 merged, 54 teammate PRs reviewed in 15 weeks), Team Lead at Delta Labs (EUR 4.4M seed), CTO at Ranova, EPFL Blue Brain (AA reviews), and 1st tech hire at RTK.io (10k+ users, acquired by Magnite).

Swiss permit holder. Open to senior/staff AI platform, full-stack lead, and founding engineer roles in Zurich, Geneva, or remote-EU.
```

---

## LinkedIn Experience Copy (Ready to Paste)

### Natzka: Senior Software Engineer (Aug 2026 - Present | Zurich, Switzerland)

```text
Joined to help build the AI team and ship production AI Assistant, MCP, and evaluation capabilities across a high-velocity TypeScript / Bun / React / Rust data intelligence platform.

- Shipped the production AI Assistant and a docked, screen-aware Chat Panel across 7 screens: browser-only ephemeral chats, prompt-injection-safe screen context outside cached instructions, bidirectional hover links between answers and screen panels/cells, and disconnect-resilient conversations.
- Built an 11-tool MCP OAuth resource server (RFC 9728 metadata, audience-bound tokens, 90s query cap) plus workflow list/start/cancel write tools with per-action permission checks and atomic human-in-the-loop approval cards.
- Built the assistant's offline evaluation harness (275 checks across 91 scored cases and 186 total cases, 20 paired refusal traps, dual-pass Bedrock EU LLM-as-judge grading, headless-Chromium replay, blind human review sheet), Langfuse tracing/ratings, and cost/context controls (47% prefix cache, 60k sliding window, per-tenant daily token budgets).
- Hardened platform security and privacy: led 15 merged IAM security fixes (+3,749 / -585), fixed CI env-secret leaks into public frontend bundles and PR-cache poisoning in deploy jobs, added whitelist chat persistence stripping customer data, and migrated inference to AWS Bedrock (EU).
- Multiplied team quality: opened 272 PRs (243 merged; +77,062 / -12,641 net lines across 977 files on main), reviewed 54 teammate PRs (46 closed, 8 open; 113 passes, 195 inline comments), built 11 Claude Code agents and 21 skills (distilling 662 review comments via 3 skeptic agents into 38 verified rules), audited tests across 9 PRs (+891 / -3,065), and authored the AI capability handover roadmap.
```

### Delta Labs AG: Team Lead / Senior Fullstack AI Engineer (Jul 2025 - Jul 2026 | Zurich, Switzerland)

```text
Lead contributor and team lead at a UZH AI spin-off building an enterprise customer-simulation platform powered by Recursive Language Models (EUR 4.4M seed round led by Cusp Capital, Mar 2026).

- Built the production AI stack end-to-end in Python on Azure and PostgreSQL + pgvector: RAG retrieval over proprietary enterprise documents (ingestion, OCR, chunking, embedding, indexing), RLM inference with schema-enforced structured outputs, durable Inngest execution, EU OpenAI routing, and throttling/retry/circuit-breaker guardrails.
- Delivered a 3,370x vector-search speedup (25s to 7ms on 162k rows) via pg_diskann (supporting full 3072-dim embeddings with zero app code changes), overcame Postgres's 256 MB JSONB limit, and built 2.7 GB+ streaming JSON ETL pipelines.
- Lifted backend test coverage from 5% to 85% (100% on async/event-driven functions; ~8,500 lines of new tests), introduced AI Agent Skills and MCP tooling team-wide, shipped a greenfield FastAPI data-service microservice, and shipped 320+ merged PRs across 8 repos in 10 months.
```

---

## GitHub Profile (`smitfire`) Bio & README Intro

**Bio (<= 160 chars):**
```text
Senior AI / Full-Stack Engineer (12+ yrs, CH). Governed production agents, OAuth MCP, cleanroom evals, Postgres/pgvector. Creator of Forewisp & ns-dsh.
```

**Profile README Intro:**
```markdown
I build governed, empirically evaluated AI systems and multi-agent engineering harnesses. Across production roles in Zurich and Geneva (Natzka, Delta Labs, Ranova, EPFL Blue Brain, RTK.io/Magnite) and open-source R&D (848 merged and 26 open PRs across `smitfire/context`, `ns-dsh`, `smitosis`, `agent-dotfiles`, `local-role-kit`, and `cv`), my work focuses on prompt-injection isolation, least-privilege OAuth MCP servers, adaptive context packing, falsifiable eval harnesses, and database/systems performance.
```
