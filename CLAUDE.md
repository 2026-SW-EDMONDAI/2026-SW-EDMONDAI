# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**SegmentFlow** — 교육영상을 세그먼트 단위로 분석해 학습 흐름을 파악하고, 학습 품질을 보존하는 광고 위치를 Agent가 추천하는 운영 도구.

현재 저장소는 **기획/설계와 초기 구현 스캐폴딩 단계**이며, `apps/web`, `apps/api`, `apps/worker`에 대한 기본 구조와 일부 구현 코드가 포함되어 있습니다.

## 예정 모노레포 구조

```
/apps
  /web        → Next.js (App Router) + TypeScript + pnpm + Tailwind CSS
  /api        → FastAPI + Uvicorn + Pydantic v2 + SQLAlchemy 2.0
  /worker     → Celery Worker
/packages
  /schemas    → API DTO, typed contracts
  /ui         → 공통 UI 컴포넌트
  /config     → lint / tsconfig / env templates
/infrastructure
  /docker     → Docker Compose (로컬 개발환경)
```

## 개발 명령어 (구현 후 사용 예정)

### 로컬 환경 전체 실행
```bash
docker compose up -d
```
컨테이너 구성: `web`, `api`, `worker`, `beat`, `rabbitmq`, `postgres`, `prometheus`, `grafana`

### Frontend (apps/web)
```bash
pnpm install
pnpm dev           # 개발 서버
pnpm build         # 프로덕션 빌드
pnpm lint          # ESLint
pnpm typecheck     # TypeScript 타입 검사
```

### Backend (apps/api)
```bash
uvicorn main:app --reload           # 개발 서버
pytest                              # 전체 테스트
pytest tests/contract/              # 계약 테스트만
pytest tests/contract/test_segments.py  # 단일 테스트 파일
alembic upgrade head                # DB 마이그레이션 적용
alembic revision --autogenerate -m "description"  # 마이그레이션 생성
```

### E2E 테스트
```bash
pnpm playwright test                # 전체 E2E 테스트
pnpm playwright test --ui           # UI 모드
```

## 시스템 아키텍처

```
[ Next.js Dashboard ]
        ↓
[ FastAPI API ]
   ├─ PostgreSQL (운영 데이터 + jsonb 반정형)
   ├─ S3 (영상, 자막, 리포트 파일)
   ├─ RabbitMQ (메시지 브로커)
   └─ Prometheus / Grafana (관측성)
        ↓
[ Celery Workers ]
   ├─ video-processing  큐
   ├─ metrics-aggregation 큐
   ├─ recommendation 큐
   └─ default 큐
```

**데이터 흐름**: 운영자 영상 업로드 → Celery 비동기 세그먼트 생성 → 학습 이벤트 수집(암묵/명시적) → 세그먼트 퍼널 스냅샷 집계 → Agent 광고 위치 추천 → 운영자 승인(Human-in-the-loop) → 성과/가드레일 모니터링

## 핵심 API 규칙

- 멀티테넌시: 모든 엔드포인트는 `/api/v1/orgs/{orgId}/...` 구조
- 이벤트 수집: `POST /player/events/batch` (플레이어 토큰 기반, clientEventId 멱등)
- 세그먼트 버전 관리: `segment_sets` + `segments` 테이블 구조
- 원시 이벤트/집계 분리: `learning_events` / `segment_metric_snapshots`

## 마일스톤 및 개발 순서

| 단계 | 목표 | 선행 의존성 |
|------|------|------------|
| M1 | 모노레포 초기화, 인증, Docker Compose, CI | 없음 |
| M2 | 영상 업로드, 자막, 세그먼트 생성/수정 | M1 |
| M3 | 이벤트 수집, 학습 퍼널 집계/시각화 | M2 |
| M4 | Agent 추천, 운영자 승인/수정/적용 | M3 |
| M5 | 성과 리포트, 가드레일, E2E QA | M4 |

**병렬 작업 규칙**: API/DB 계약이 고정된 후에만 FE/BE 병렬 구현 가능. 계약 미확정 상태에서 병렬 구현 금지.

## Agent 워크플로우 (.github/agents/)

이 저장소는 GitHub Copilot/Claude 기반 에이전트 협업 구조를 사용합니다.

- **공통 제약**: `.github/agents/shared/common-context.md`
- **마일스톤 워크플로우**: `.github/agents/workflows/m1-foundation.md` ~ `m5-report-stabilization.md`
- **역할별 프롬프트**: `.github/agents/prompts/01-platform-bootstrap.md` ~ `08-metrics-observability.md`
- **오케스트레이터**: `.github/agents/orchestrator/system-prompt.md` + `runbook.md`

### handoff 보고 형식

각 작업 완료 시 `.github/agents/workflows/handoff-schema.yaml` 형식으로 보고해야 합니다. PR 본문에 반드시 포함:
- handoff YAML 요약
- `pytest` / `playwright` 테스트 결과
- 스키마 변경 시: 마이그레이션 파일 + 롤백 전략

### 충돌 해결 우선순위

- 스키마 충돌 → Data Modeling Agent 우선
- API 충돌 → Backend API Agent 우선
- UI 충돌 → Frontend Dashboard Agent 우선

## Source of Truth 문서

| 문서 | 경로 |
|------|------|
| 제품 비전/KPI | `docs/prd.md` |
| MVP 마일스톤/이슈 | `docs/mvp.md` |
| 기술 스택 선정 근거 | `docs/techstack.md` |
| API 엔드포인트/DTO | `docs/api.md` |
| DB 스키마/ERD | `docs/db-schema.md` |
| UX/IA 화면 구조 | `docs/IA-wireframe.md` |

## MVP 범위 제약

다음 기능은 MVP에서 **명시적으로 제외**됩니다:
- 개인화 광고 추천
- 실시간 광고 입찰 최적화
- 운영자 승인 없는 자동 광고 삽입
- Vector DB / Kafka / Kubernetes (MVP 이후 검토)
