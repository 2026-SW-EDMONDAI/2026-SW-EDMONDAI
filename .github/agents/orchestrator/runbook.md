# Orchestrator Runbook

## 1. Sprint Start

- 현재 마일스톤과 게이트를 `workflows/m*.md`에서 확정
- 이슈를 agent owner 기준으로 분해
- API/DB 계약 변경 여부를 먼저 판정

## 2. Task Assignment Rule

- 한 이슈에 owner 에이전트 1명 지정
- `inputs/contracts/expected outputs/tests`를 이슈 본문에 명시
- 병렬 작업은 계약 고정 후 시작

## 3. Merge Rule

- PR 본문에 handoff YAML 요약 필수
- `pytest`/`playwright` 결과 링크 필수
- 스키마 변경 시 마이그레이션 파일 + 롤백 전략 필수

## 4. Escalation

- 스키마 충돌: Data Modeling Agent 우선
- API 충돌: Backend API Agent 우선
- UI 충돌: Frontend Dashboard Agent 우선
- 품질 게이트: QA & Reliability Agent 우선
