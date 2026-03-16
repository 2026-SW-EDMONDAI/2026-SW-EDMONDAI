# SegmentFlow

교육영상 세그먼트 기반 학습 퍼널 분석 및 Agent 광고 위치 추천 시스템

SegmentFlow는 교육영상을 세그먼트 단위로 분석해 학습 흐름을 파악하고, 학습 품질을 최대한 보존하는 광고 위치를 추천하는 운영 도구입니다.

## 프로젝트 목적

- 영상 단위 평균 지표를 넘어 세그먼트 단위로 학습 흐름을 분석
- 암묵적 학습 신호(시청 행동) + 명시적 학습 신호(직접 반응) 통합 해석
- Agent 추천 + 운영자 승인(Human-in-the-loop) 기반 광고 위치 의사결정
- 광고 성과와 학습 가드레일 KPI를 함께 관리

## MVP 범위

### 포함

- 교육영상 업로드 및 자막 연동
- 세그먼트 자동 생성
- 세그먼트 단위 학습 퍼널 지표 산출
- 이해도 체크(명시적 신호) 수집 및 분석
- Agent 광고 위치 추천
- 추천 근거 확인 및 운영자 승인/수정/적용

### 제외

- 개인화 광고 추천
- 실시간 광고 입찰 최적화
- 운영자 승인 없는 자동 광고 삽입
- 고급 실험 자동화

## 핵심 사용자

- 교육 플랫폼 운영자: 데이터 기반 광고 의사결정
- 콘텐츠 기획자: 학습 민감 구간 파악 및 콘텐츠 개선
- 광고 운영 매니저: 학습 품질을 해치지 않는 슬롯 실험

## 기술 스택 (권장안)

- Frontend: Next.js (App Router), TypeScript, pnpm
- Backend: FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0
- Database: PostgreSQL
- Async/Queue: Celery + RabbitMQ
- Storage: Amazon S3
- Infra: Docker Compose(dev), AWS ECS Fargate(prod)
- Observability: OpenTelemetry, Prometheus, Grafana
- Testing: pytest, Playwright

## 아키텍처 개요

1. 운영자가 영상을 업로드하고 분석을 실행
2. 비동기 워커(Celery)가 자막/영상 기반 세그먼트 생성 및 지표 집계
3. 학습 이벤트(암묵/명시/광고)를 수집하고 세그먼트 퍼널 스냅샷 계산
4. Agent가 광고 위치 후보를 추천하고 근거/위험도를 제시
5. 운영자가 승인/수정/반려 후 적용
6. 적용 후 광고 성과와 학습 가드레일 지표를 비교

## API/데이터 모델 핵심

- 멀티테넌시: `/api/v1/orgs/{orgId}/...`
- 이벤트 수집: 플레이어 토큰 기반 배치 이벤트 수집
- 세그먼트 버전 관리: `segment_sets` + `segments`
- 원시 이벤트/집계 분리: `learning_events` / `segment_metric_snapshots`
- 추천 이력 관리: `recommendation_runs` / `recommendation_candidates` / `recommendation_reviews`

## 문서 안내

- [PRD](docs/prd.md): 제품 비전, 문제 정의, KPI, 사용자
- [MVP](docs/mvp.md): 마일스톤(M1~M5), 이슈, 완료 기준
- [Tech Stack](docs/techstack.md): 레이어별 기술 선정 근거
- [API 명세](docs/api.md): 엔드포인트 규칙, 권한, DTO
- [DB 스키마](docs/db-schema.md): ERD, 테이블/Enum 설계
- [IA/Wireframe](docs/IA-wireframe.md): 화면 구조, 핵심 UX 흐름
- [서식일체](docs/서식일체_통합본.md): 프로젝트 신청/수행 계획서 템플릿
- [GitHub Agents Hub](.github/agents/README.md): GitHub 기반 에이전트 실행 허브
- [Agent Prompts](.github/agents/prompts/01-platform-bootstrap.md): 역할별 분해 프롬프트 시작점
- [Agent Workflow](.github/agents/workflows/00-master-workflow.md): 마일스톤 기반 실행 워크플로우
- [Orchestrator Prompt](.github/agents/orchestrator/system-prompt.md): 워크플로우 중개용 오케스트레이터 프롬프트

## 현재 저장소 상태

현재 저장소는 문서 중심의 기획/설계 단계입니다.

- 루트: `docs/` + 본 `README.md`
- 구현 코드(`apps/web`, `apps/api`, `apps/worker`)는 아직 생성 전

## 다음 단계 제안

1. 모노레포 구조 생성 (`apps/web`, `apps/api`, `apps/worker`, `packages/*`)
2. Docker Compose 기반 로컬 개발환경 구성
3. M1 이슈(인증, 공통 DB, 기본 UI Shell, CI)부터 구현 시작
