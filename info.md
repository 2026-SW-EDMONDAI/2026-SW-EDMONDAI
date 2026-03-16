# SegmentFlow 워크플로우 이해용 인포그래픽 이미지 프롬프트

아래 프롬프트를 그대로 이미지 생성 모델에 입력하면, 초보자도 SegmentFlow GitHub Agents 운영 흐름을 한눈에 이해할 수 있는 인포그래픽 이미지를 만들 수 있습니다.

## 메인 프롬프트

```text
Create a clean, modern onboarding infographic in Korean for beginner contributors who need to quickly understand the SegmentFlow GitHub Agents workflow.

Main title: "SegmentFlow GitHub Agents 워크플로우 한눈에 보기"
Subtitle: "초보자를 위한 M1~M5 기반 작업 진행 흐름"

Goal:
- Make the workflow feel easy to follow at a glance
- Show the exact order of work from reading documents to PR and handoff
- Emphasize milestone-based execution, contract-first rules, validation, and reporting

Canvas and layout:
- Vertical poster infographic, 4:5 ratio
- Bright background with high readability
- Clear section dividers and strong visual hierarchy
- Center: large numbered workflow path from 1 to 9
- Left side: documents and reference files
- Right side: rules, checkpoints, and deliverables
- Bottom: milestone timeline M1 to M5 and end-to-end flow

Visual style:
- Professional but friendly onboarding style
- Flat vector infographic with light depth and soft shadows
- Color palette: navy, teal, sky blue, warm orange for warnings, light gray background
- Use clean Korean typography, bold headings, short labels, compact captions
- Use icons for document, orchestrator, agent, API contract, database contract, test, YAML handoff, pull request, milestone gate
- Add arrows, connector lines, and step badges for a guided learning experience

Must include these exact workflow sections in order:

1. "시작 준비"
   - README.md 읽기
   - common-context.md 읽기
   - 00-master-workflow.md 읽기
   - system-prompt.md 읽기
   - runbook.md 읽기
   - small caption: "먼저 전체 규칙과 진행 순서를 이해"

2. "현재 마일스톤 선택"
   - M1 Foundation
   - M2 Ingestion & Segmentation
   - M3 Funnel Analytics
   - M4 Recommendation & Review
   - M5 Report & Stabilization
   - highlight 3 checks: Owner, Must Deliver, Exit Gate

3. "오케스트레이터에게 작업 분해 요청"
   - include callout text: owner agent
   - include callout text: inputs / contracts / expected outputs / tests
   - include callout text: 병렬 가능 시점은 계약 고정 후
   - show orchestrator as control tower

4. "담당 에이전트 실행"
   - show 8 specialist agents as small cards
   - Platform Bootstrap Agent
   - Frontend Dashboard Agent
   - Backend API Agent
   - Data Modeling Agent
   - Async Pipeline Agent
   - Recommendation Logic Agent
   - QA & Reliability Agent
   - Metrics & Observability Agent

5. "병렬 작업 전 체크"
   - API 계약 확정
   - DB 스키마 변경 여부 확정
   - 이슈 본문에 inputs / contracts / expected outputs / tests 명시
   - warning badge: "계약 미확정 상태 병렬 구현 금지"
   - allowed parallel examples: FE and BE, Pipeline and Recommendation

6. "구현 후 검증"
   - pytest 결과
   - playwright 결과
   - migration file
   - rollback strategy
   - caption: "기능 구현만이 아니라 검증 로그까지 남긴다"

7. "handoff 보고 작성"
   - show YAML card
   - include fields: agent, phase, status, code_changes, schema_changes, api_changes, tests, contracts, risks, next_actions
   - emphasize handoff-schema.yaml compliance

8. "PR 체크리스트"
   - handoff YAML summary
   - test logs or links
   - migration and rollback strategy when schema changes exist
   - show GitHub pull request panel visual

9. "완료 판정"
   - pass milestone Exit Gate
   - no break in end-to-end flow
   - display final E2E chain clearly:
     upload -> segment -> funnel -> recommendation -> approval/apply -> report/guardrail

Side panel content:
- "핵심 원칙"
- 마일스톤 기반 진행
- Owner agent 중심 책임
- 계약 고정 후 병렬 작업
- handoff-schema.yaml 필수
- 테스트와 보고까지 완료해야 종료

Bottom section:
- A simple horizontal milestone timeline M1 -> M2 -> M3 -> M4 -> M5
- Small note under timeline: "각 단계는 Exit Gate 통과 후 다음 단계로 이동"

Text style:
- All main labels in Korean
- File names and agent names can remain in English
- No lorem ipsum or decorative fake text
- Every label should be operational and instructional

Output quality:
- Presentation-ready
- Crisp, organized, easy to scan
- Suitable for README, onboarding docs, or team presentation slide
```

## 짧은 버전 프롬프트

```text
초보자를 위한 SegmentFlow GitHub Agents 워크플로우 인포그래픽을 한국어로 제작해줘. 문서 읽기, 마일스톤 선택, 오케스트레이터 작업 분해, 담당 에이전트 실행, 계약 고정 후 병렬 작업, pytest와 playwright 검증, handoff YAML 작성, PR 체크리스트, Exit Gate 통과와 E2E 완료 판정까지 1부터 9까지 순서형 플로우로 보여줘. M1부터 M5까지 타임라인과 8개 specialist agent 카드도 포함하고, 깔끔한 B2B 온보딩 스타일의 벡터 인포그래픽으로 구성해줘.
```