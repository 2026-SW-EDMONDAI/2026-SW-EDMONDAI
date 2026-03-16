# SegmentFlow Agents & Workflow 인포그래픽 프롬프트

아래 프롬프트를 그대로 이미지 생성 모델(예: Midjourney, DALL·E, SDXL 기반 툴)에 입력해 사용하세요.

---

## Master Prompt (전문가 스타일)

```text
Create a professional enterprise-grade infographic in Korean for a software engineering audience.

Title: "SegmentFlow GitHub Agents 운영 아키텍처"
Subtitle: "MVP(M1~M5) 달성을 위한 Agent-Orchestrator Workflow"

Canvas & Layout:
- Vertical 4:5 ratio, 1600x2000px, clean grid layout, high readability
- Top: Executive summary band (3 key bullets)
- Middle-left: Agent architecture map
- Middle-right: Milestone workflow timeline (M1→M5)
- Bottom: GitHub execution artifacts + governance checklist
- Add directional arrows with clear handoff flow

Visual Style:
- Premium B2B infographic, minimal and elegant
- Flat vector style + subtle depth, no cartoon style
- Color palette: deep navy, slate gray, teal accents, soft amber highlights
- Typography: modern sans-serif, bold section headers, compact body labels
- Use consistent iconography (database, API, queue, dashboard, test, metrics, orchestration)
- White/light background, strong contrast for accessibility

Content Requirements (must include exact structure):
1) "GitHub Agents Hub" block
   - .github/agents/README.md
   - shared/common-context.md
   - prompts/*.md (8 specialist agents)
   - workflows/*.md (master + M1~M5 + handoff-schema.yaml)
   - orchestrator/system-prompt.md, runbook.md

2) "8 Specialist Agents" block (grouped cards)
   - Platform Bootstrap Agent
   - Frontend Dashboard Agent
   - Backend API Agent
   - Data Modeling Agent
   - Async Pipeline Agent
   - Recommendation Logic Agent
   - QA & Reliability Agent
   - Metrics & Observability Agent

3) "Milestone Workflow" horizontal timeline
   - M1 Foundation
   - M2 Ingestion & Segmentation
   - M3 Funnel Analytics
   - M4 Recommendation & Review
   - M5 Report & Stabilization
   - Each milestone shows: owner agent(s), key deliverable, exit gate

4) "Orchestrator Control Plane" central overlay
   - Contract freeze before parallel execution
   - Handoff schema enforcement
   - Conflict resolution by contract owner
   - Gate-based progression

5) "GitHub Ops Integration" footer
   - Issue Template: .github/ISSUE_TEMPLATE/agent-task.yml
   - PR Template: .github/pull_request_template.md
   - Required outputs: tests, contracts, risks, next actions

6) "Core Principles" side panel
   - MVP scope only
   - Human-in-the-loop recommendation
   - API/DB contract-first development
   - Async-first pipeline
   - Quality gates + observability

Text Tone:
- Professional, concise, consultant-level clarity
- Korean labels for sections; English allowed only for file paths and agent names
- No decorative filler text; all text must be actionable

Output Quality:
- Crisp vector-like rendering
- Balanced whitespace and alignment
- Ready for executive presentation deck
- Include legend for arrow meaning: sequential, parallel, gated
```

---

## Variant Prompt A (초간결 발표용)

```text
Design a clean executive infographic (Korean) titled "SegmentFlow Agent Workflow" showing:
- 8 specialist agents,
- orchestrator control plane,
- M1~M5 gated timeline,
- GitHub templates and handoff schema.
Use enterprise style, navy/teal palette, strong hierarchy, minimal text, presentation-ready.
```

## Variant Prompt B (기술 상세 강조)

```text
Create a technical architecture infographic in Korean focused on contract-first multi-agent delivery.
Show .github/agents folder decomposition, role-by-role prompts, M1~M5 exit gates, and orchestrator governance rules.
Add explicit arrows for sequential vs parallel execution and a YAML handoff schema callout.
Style: premium engineering documentation visual.
```

## Variant Prompt C (온보딩 교육용)

```text
Generate an onboarding infographic in Korean for new contributors explaining how to execute SegmentFlow agents via GitHub.
Include: where to start, which file to open first, how to pick agent by milestone, how to report handoff, and how PR validation works.
Keep it simple, highly readable, and operationally precise.
```
