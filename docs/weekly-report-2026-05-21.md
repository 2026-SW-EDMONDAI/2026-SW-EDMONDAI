# 주간 보고 — 2026년 5월 3주차 (05.19 ~ 05.21)

## 1. 금주 진행 사항

### 1.1 M1 마일스톤 완료 확인

| 이슈 | 내용 | 상태 |
|------|------|------|
| #2 M1-01 | 모노레포 초기 구성 (pnpm workspace) | ✅ 완료 |
| #3 M1-02 | Docker Compose 개발환경 구성 (7개 서비스) | ✅ 완료 |
| #4 M1-03 | FastAPI 기본 앱 구성 | ✅ 완료 |
| #5 M1-04 | Next.js 기본 앱 및 레이아웃 구성 | ✅ 완료 |
| #6 M1-05 | 인증/권한 모델 구현 (JWT) | ✅ 완료 |
| #7 M1-06 | DB 마이그레이션 체계 구축 (Alembic) | ✅ 완료 |
| #8 M1-07 | 로깅/모니터링 기본 세팅 (Prometheus + Grafana) | ✅ 완료 |
| #9 M1-08 | CI 기본 파이프라인 (GitHub Actions) | ✅ 완료 |

### 1.2 M2 마일스톤 구현 (이번 주 신규)

현재 브랜치: `m1/infra-setup`

| 이슈 | 내용 | 구현 산출물 |
|------|------|-------------|
| #12 M2-1 | DB 스키마 확장 | `models/video.py`, `models/segment.py`, `0002_m2_ingestion_segmentation.py` |
| #13 M2-2 | 영상 관리 API | `routes/videos.py`, `routes/captions.py`, `services/video_service.py`, 계약 테스트 2종 |
| #14 M2-3 | 세그먼트 버전관리 API | `routes/segments.py`, `services/segment_service.py`, 계약 테스트 1종 |
| #15 M2-4 | 분석 워커 (VTT/SRT 파싱 + 자동 세그먼트) | `worker/tasks/video_processing.py`, 통합 테스트 1종 |
| #16 M2-5 | 프론트엔드 영상/세그먼트 UI | 페이지 4개 + 컴포넌트 5개 |
| #17 M2-6 | E2E 검증 시나리오 | `tests/e2e/videos.spec.ts` (3개 시나리오) |

### 1.3 주요 기술 구현 내용

#### 백엔드 (FastAPI)
- **6개 테이블** 추가 마이그레이션 (`video_assets`, `caption_tracks`, `caption_cues`, `video_signal_configs`, `segment_sets`, `segments`)
- **16개 REST 엔드포인트** 구현 — 영상 CRUD, 신호설정, 자막, 세그먼트 버전관리(clone/finalize), 분할/병합
- **도메인 규칙 적용** — finalized 세트 수정 시 409, 범위 외 분할 422, 비연속 병합 422

#### 워커 (Celery)
- VTT / SRT 파서 자체 구현
- 자막 → 5분 단위 자동 세그먼트 생성 로직
- 멱등성 보장 (중복 실행 safe), max_retries=3

#### 프론트엔드 (Next.js)
- `lib/api.ts` API 클라이언트 (videoApi / segmentApi / captionApi)
- 영상 목록 (상태 필터 + 검색 + 페이지네이션)
- 영상 업로드 폼 (multipart, 신호설정 포함)
- 세그먼트 타임라인 시각화 + 편집 (분할/확정/복제)

---

## 2. 금주 활동

| 일자 | 활동 내용 |
|------|-----------|
| 05.19 | 프로젝트 현황 분석, 이슈 #12~#17 요구사항 파악 |
| 05.20 | M2 설계 검토 (docs/api.md, docs/db-schema.md 기반) |
| 05.21 | 이슈 #12~#17 전체 구현 완료 및 이슈 코멘트 작성 |

---

## 3. 차주 계획 (05.26 ~ 05.30)

### 3.1 PR 작성 및 리뷰

| 순서 | 작업 | 내용 |
|------|------|------|
| 1 | M2 PR 작성 | `m1/infra-setup` → `main` PR 생성, 이슈 #12~#17 연결 |
| 2 | PR 설명 작성 | handoff YAML 포함 (`.github/agents/workflows/handoff-schema.yaml` 형식) |
| 3 | CI 통과 확인 | lint / typecheck / build / pytest 전체 green 확인 |
| 4 | 코드 리뷰 반영 | Copilot/팀원 리뷰 피드백 수정 후 재검토 |
| 5 | PR 머지 | squash merge → main 반영 |

### 3.2 M3 이슈 생성 준비

M2 완료 후 M3(학습 이벤트 수집 + 퍼널 집계) 이슈 사전 설계.

| 예정 이슈 | 내용 | 선행 조건 |
|-----------|------|-----------|
| M3-1 | DB 스키마 확장 — `learner_sessions`, `learning_events`, `segment_metric_snapshots` | M2 머지 완료 |
| M3-2 | 이벤트 수집 API — `POST /player/events/batch` (플레이어 토큰, 멱등성) | M3-1 완료 |
| M3-3 | 메트릭 집계 워커 — `segment_metric_snapshots` 배치 집계 Celery 태스크 | M3-1 완료 |
| M3-4 | 학습 퍼널 API — `GET /videos/{id}/funnel` | M3-2, M3-3 완료 |
| M3-5 | 프론트엔드 — 퍼널 시각화 (완료율/이탈률/재시청률 차트) | M3-4 완료 |
| M3-6 | E2E 검증 — 이벤트 수집 → 집계 → 퍼널 조회 전체 흐름 | M3-1~5 완료 |

### 3.3 기술 검토 항목

- [ ] `learning_events` 테이블 월별 파티셔닝 전략 결정 (`docs/db-schema.md` 기준)
- [ ] 플레이어 토큰 서명 방식 결정 (JWT 파생 vs 별도 발급)
- [ ] 메트릭 집계 배치 주기 결정 (실시간 near-realtime vs 1시간 배치)
- [ ] 프론트엔드 차트 라이브러리 선정 (Recharts / Chart.js 등)

---

## 4. 이슈/블로커

| 항목 | 내용 | 대응 방안 |
|------|------|-----------|
| 파일 스토리지 | MVP에서 로컬 파일시스템 임시 사용 중 | M3 전에 S3 연동 또는 Docker volume 정책 확정 필요 |
| Playwright 미설치 | `apps/web/package.json`에 Playwright 미포함 | PR 시 `@playwright/test` 패키지 추가 필요 |
| 테스트 DB | 계약 테스트가 SQLite in-memory 사용 | PostgreSQL 전용 타입(JSONB 등) 호환성 CI 환경에서 추가 확인 필요 |
