# Migration from docs/agents

기존 문서는 실행 중심 구조로 `.github/agents`에 분해되었습니다.

## 매핑

- `docs/agents/agent-prompts.md`
  - `.github/agents/shared/common-context.md`
  - `.github/agents/prompts/*.md`
- `docs/agents/workflow.md`
  - `.github/agents/workflows/00-master-workflow.md`
  - `.github/agents/workflows/m1-*.md` ~ `m5-*.md`
  - `.github/agents/workflows/handoff-schema.yaml`
- `docs/agents/orchestrator-prompt.md`
  - `.github/agents/orchestrator/system-prompt.md`
  - `.github/agents/orchestrator/runbook.md`

## 운영 권장

- 이슈 생성: `.github/ISSUE_TEMPLATE/agent-task.yml`
- PR 보고: `.github/pull_request_template.md`
