# SegmentFlow 에이전트 운영 가이드 (초보자용)

이 문서는 **처음 참여하는 사람도 그대로 따라할 수 있도록**
GitHub Agents 운영 절차를 단계별로 정리한 실행 가이드입니다.

---

## 0) 먼저 이해할 핵심

- 이 저장소는 마일스톤(M1~M5) 기반으로 진행합니다.
- 각 마일스톤에는 **Owner(주 담당 에이전트)**가 있고, Supporting 에이전트가 보조합니다.
- API/DB 계약이 고정되기 전에는 병렬 구현을 시작하지 않습니다.
- 결과 보고는 반드시 `handoff-schema.yaml` 형식을 따릅니다.

참고 문서:
- `.github/agents/README.md`
- `.github/agents/orchestrator/system-prompt.md`
- `.github/agents/orchestrator/runbook.md`
- `.github/agents/shared/common-context.md`
- `.github/agents/workflows/00-master-workflow.md`

---

## 1) 시작 준비 (문서 열기)

아래 파일을 순서대로 열어 읽습니다.

1. `.github/agents/README.md`
2. `.github/agents/shared/common-context.md`
3. `.github/agents/workflows/00-master-workflow.md`
4. `.github/agents/orchestrator/system-prompt.md`
5. `.github/agents/orchestrator/runbook.md`

> 목표: “무슨 순서로 진행하고, 어떤 규칙으로 충돌을 해결하는지” 이해하기

---

## 2) 현재 작업 마일스톤 선택

`workflows` 폴더에서 이번 작업 단계를 고릅니다.

- M1: `.github/agents/workflows/m1-foundation.md`
- M2: `.github/agents/workflows/m2-ingestion-segmentation.md`
- M3: `.github/agents/workflows/m3-funnel-analytics.md`
- M4: `.github/agents/workflows/m4-recommendation-review.md`
- M5: `.github/agents/workflows/m5-report-stabilization.md`

각 파일에서 아래 3가지를 확인합니다.
- **Owner** (누가 주도하는가)
- **Must Deliver** (반드시 만들어야 할 산출물)
- **Exit Gate** (완료 판정 조건)

---

## 3) 오케스트레이터에게 작업 분해 요청

Copilot Chat에 아래처럼 요청합니다.

### 복붙 템플릿 (오케스트레이터)

```text
M2 기준으로 작업을 분해해줘.
다음을 반드시 포함해줘:
1) owner 에이전트
2) inputs/contracts/expected outputs/tests
3) 병렬 가능 시점(계약 고정 후)
4) 단계별 검증 명령
```

> 팁: M2 대신 M1/M3/M4/M5로 바꿔서 사용하세요.

---

## 4) 담당 에이전트 프롬프트 실행

해당 역할 프롬프트 파일을 열고, 그대로 실행 요청합니다.

예시 프롬프트 파일:
- `.github/agents/prompts/01-platform-bootstrap.md`
- `.github/agents/prompts/02-frontend-dashboard.md`
- `.github/agents/prompts/03-backend-api.md`
- `.github/agents/prompts/04-data-modeling.md`
- `.github/agents/prompts/05-async-pipeline.md`
- `.github/agents/prompts/06-recommendation-logic.md`
- `.github/agents/prompts/07-qa-reliability.md`
- `.github/agents/prompts/08-metrics-observability.md`

### 복붙 템플릿 (에이전트 실행)

```text
Backend API Agent 역할로 작업해줘.
범위: /api/v1/orgs/{orgId}/...
요구사항:
- 구현 계획
- 코드 변경 목록
- API/스키마 영향
- pytest 검증 명령
- 위험요소 및 대응
```

---

## 5) 병렬 작업 시작 전 체크 (중요)

`runbook.md` 기준으로 아래를 먼저 고정합니다.

- API 계약 변경 여부 확정
- DB 스키마 변경 여부 확정
- 이슈 본문에 `inputs/contracts/expected outputs/tests` 명시

그 다음에만 병렬 작업을 시작합니다.

- 가능: FE/BE 병렬, Pipeline/Recommendation 병렬
- 금지: 계약 미확정 상태에서 병렬 구현

---

## 6) 구현 후 검증 수행

프로젝트에서 사용하는 테스트 결과를 남깁니다.

- `pytest` 결과
- `playwright` 결과

스키마 변경이 있으면 반드시 추가:
- 마이그레이션 파일
- 롤백 전략

---

## 7) handoff 보고 작성

아래 파일 형식에 맞춰 작성합니다.
- `.github/agents/workflows/handoff-schema.yaml`

### 최소 작성 항목

- `agent`
- `phase` (M1~M5)
- `status` (done/blocked/needs-review)
- `outputs.code_changes`
- `outputs.schema_changes`
- `outputs.api_changes`
- `outputs.tests`
- `contracts.producer`
- `contracts.consumer`
- `risks`
- `next_actions`

### handoff 예시

```yaml
handoff:
  agent: backend-api-agent
  phase: M2
  status: done
  outputs:
    code_changes: ["apps/api/routes/segments.py", "apps/api/services/segment_service.py"]
    schema_changes: ["segments.version"]
    api_changes: ["POST /api/v1/orgs/{orgId}/segments/review"]
    tests: ["pytest tests/contract/test_segments.py"]
  contracts:
    producer: "세그먼트 리뷰 API는 version 충돌 시 409를 반환한다"
    consumer: "프론트엔드는 409 수신 시 최신 version 재조회 후 재시도한다"
  risks:
    - "대량 세그먼트 처리 시 응답 지연 가능성"
  next_actions:
    - "QA agent가 동시 수정 충돌 시나리오 검증"
```

---

## 8) PR 올릴 때 체크리스트

PR 본문에 다음이 있어야 합니다.

- handoff YAML 요약
- 테스트 결과 링크/로그 (`pytest`, `playwright`)
- (스키마 변경 시) 마이그레이션 + 롤백 전략

관련 템플릿:
- `.github/pull_request_template.md`

---

## 9) 완료 판정 방법

아래 두 가지를 모두 만족해야 완료입니다.

1. 해당 마일스톤의 `Exit Gate`를 통과
2. E2E 흐름 단절 없음
   - upload → segment → funnel → recommendation → approval/apply → report/guardrail

---

## 10) 가장 쉬운 시작 순서 (처음 30분)

1. `README.md` + `common-context.md` 읽기 (10분)
2. 이번 마일스톤 파일 1개 선택 후 Owner 확인 (5분)
3. 오케스트레이터 템플릿으로 작업 분해 요청 (5분)
4. 담당 프롬프트 파일로 첫 구현 요청 (10분)

이 순서로 시작하면, 초보자도 빠르게 팀 규칙에 맞춰 작업을 진행할 수 있습니다.
