# SegmentFlow GitHub Agents Hub

GitHub 기반 협업에서 에이전트를 실행하기 위한 표준 폴더입니다.

## 구조

- `shared/`: 공통 제약/출력 규격
- `prompts/`: 역할별 에이전트 프롬프트 (1 agent = 1 file)
- `workflows/`: 마일스톤/핸드오프/병렬 규칙
- `orchestrator/`: 오케스트레이터 시스템 프롬프트 및 운영 런북

## 빠른 시작

1. 오케스트레이터: `orchestrator/system-prompt.md`
2. 공통 제약 로드: `shared/common-context.md`
3. 현재 마일스톤 워크플로우 선택: `workflows/m1-foundation.md` ~ `workflows/m5-stabilization.md`
4. 담당 에이전트 프롬프트 실행: `prompts/*.md`
5. 결과는 `workflows/handoff-schema.yaml` 형식으로 보고

## GitHub 운영 연동

- 이슈 템플릿: `.github/ISSUE_TEMPLATE/agent-task.yml`
- PR 템플릿: `.github/pull_request_template.md`
- 이전 문서 매핑: `.github/agents/MIGRATION.md`

## Source of Truth

- 제품/범위: `docs/mvp.md`
- API 계약: `docs/api.md`
- DB 계약: `docs/db-schema.md`
- UX/IA: `docs/IA-wireframe.md`
- 기술 선택: `docs/techstack.md`
