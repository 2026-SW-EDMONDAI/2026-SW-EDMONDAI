# M1 Foundation — 작업 분해서

---

## 1) Owner / Supporting 에이전트

| 역할 | 에이전트 | 담당 범위 |
|------|---------|----------|
| **Owner** | Platform Bootstrap Agent | 모노레포 골격, Docker Compose, CI |
| Supporting | Data Modeling Agent | Core schema + Alembic migration |
| Supporting | Metrics & Observability Agent | Prometheus/Grafana 컨테이너 + health metric |
| Supporting | QA & Reliability Agent | CI baseline + health 검증 테스트 |

---

## 2) 태스크별 Inputs / Contracts / Expected Outputs / Tests

### Task 1: 모노레포 골격 (monorepo-scaffold)

| 항목 | 내용 |
|------|------|
| **Inputs** | `docs/techstack.md` 폴더 구조 (§6) |
| **Contracts** | `apps/web`, `apps/api`, `apps/worker`, `packages/schemas`, `packages/ui`, `packages/config`, `infrastructure/docker` 존재 |
| **Expected Outputs** | pnpm workspace 설정 (`pnpm-workspace.yaml`), `apps/api/pyproject.toml`, root `package.json`, `.gitignore`, `.env.example` |
| **Tests** | `pnpm install` 성공, `pip install -e apps/api` 성공 |

### Task 2: Docker Compose 기본 구성

| 항목 | 내용 |
|------|------|
| **Inputs** | techstack §4.6 컨테이너 목록 |
| **Contracts** | 서비스: `web`, `api`, `worker`, `beat`, `postgres`, `rabbitmq`, `prometheus`, `grafana` |
| **Expected Outputs** | `docker-compose.yml`, 각 서비스 `Dockerfile`, `.env.example` 환경변수 |
| **Tests** | `docker compose up -d` → 전 컨테이너 healthy |

### Task 3: FastAPI 기본 앱 + Health/Version

| 항목 | 내용 |
|------|------|
| **Inputs** | `docs/api.md` 공통 엔드포인트 정의 |
| **Contracts** | `GET /health` → `{"status":"ok"}`, `GET /version` → `{"version":"0.1.0"}`, `GET /docs` → Swagger UI |
| **Expected Outputs** | `apps/api/main.py`, `apps/api/routes/health.py`, `apps/api/core/config.py` |
| **Tests** | `pytest tests/test_health.py` — 200 응답, JSON 스키마 검증 |

### Task 4: Core Schema + Alembic Migration

| 항목 | 내용 |
|------|------|
| **Inputs** | `docs/db-schema.md` §4 Core Schema (organizations, users, organization_members, videos) |
| **Contracts** | M1에서는 Core 4개 테이블만. Enum: `video_status`. FK 관계 정의 |
| **Expected Outputs** | `apps/api/alembic/`, `apps/api/models/`, 초기 migration 파일 |
| **Tests** | `alembic upgrade head` 성공, `alembic downgrade -1` 성공 (롤백 검증) |

### Task 5: Next.js Shell (빈 대시보드)

| 항목 | 내용 |
|------|------|
| **Inputs** | techstack §4.1 |
| **Contracts** | App Router 기반, `/` → 대시보드 레이아웃, `/login` → 로그인 페이지 (스텁) |
| **Expected Outputs** | `apps/web/` Next.js 프로젝트, Tailwind 설정, 기본 layout + page |
| **Tests** | `pnpm build` 성공, `pnpm lint` 통과, `pnpm typecheck` 통과 |

### Task 6: JWT 인증 기본 구조

| 항목 | 내용 |
|------|------|
| **Inputs** | `docs/api.md` 인증 섹션, 멀티테넌시 `/api/v1/orgs/{orgId}/...` 패턴 |
| **Contracts** | JWT 발급/검증, `org_id` context 미들웨어, 인증 실패 시 401 |
| **Expected Outputs** | `apps/api/core/auth.py`, `apps/api/core/deps.py`, `apps/api/routes/auth.py` |
| **Tests** | `pytest tests/test_auth.py` — 토큰 발급, 검증, 만료, 잘못된 토큰 401 |

### Task 7: CI Baseline

| 항목 | 내용 |
|------|------|
| **Inputs** | 각 앱의 lint/test/build 명령 |
| **Contracts** | PR마다 자동 실행: lint, typecheck, pytest, build |
| **Expected Outputs** | `.github/workflows/ci.yml` |
| **Tests** | GitHub Actions에서 정상 통과 |

---

## 3) 병렬 가능 시점 (계약 고정 후)

```
Phase A (순차 — 계약 고정)
├── Task 1: 모노레포 골격        ← 모든 작업의 선행
├── Task 3: FastAPI 기본 앱      ← API 계약 고정
└── Task 4: Core Schema         ← DB 계약 고정

Phase B (병렬 가능 — Phase A 완료 후)
├── Task 2: Docker Compose      ← 앱 구조 확정 후
├── Task 5: Next.js Shell       ← API 계약 고정 후 FE 독립 작업
└── Task 6: JWT 인증             ← API + DB 구조 확정 후

Phase C (Phase B 완료 후)
└── Task 7: CI Baseline         ← 모든 앱/테스트 존재 후
```

**핵심 규칙**: Task 1 → Task 3, 4 (순차) → 나머지 병렬 → CI 마지막

---

## 4) 단계별 검증 명령

```bash
# Task 1: 모노레포 골격
pnpm install                          # FE 의존성 설치 확인
pip install -e "apps/api[dev]"        # BE 의존성 설치 확인
ls apps/web apps/api apps/worker packages/schemas packages/ui packages/config

# Task 2: Docker Compose
docker compose up -d
docker compose ps                     # 전 컨테이너 상태 확인
docker compose logs api --tail=20     # API 로그 확인

# Task 3: FastAPI Health/Version
curl http://localhost:8000/health     # {"status":"ok"}
curl http://localhost:8000/version    # {"version":"0.1.0"}
curl http://localhost:8000/docs       # Swagger UI 접근

# Task 4: Core Schema Migration
cd apps/api
alembic upgrade head                  # 마이그레이션 적용
alembic downgrade -1                  # 롤백 검증
alembic upgrade head                  # 재적용

# Task 5: Next.js Shell
cd apps/web
pnpm build                            # 빌드 성공
pnpm lint                             # ESLint 통과
pnpm typecheck                        # TypeScript 타입 검사

# Task 6: JWT 인증
cd apps/api
pytest tests/test_auth.py -v          # 인증 테스트

# Task 7: CI
# GitHub에 push 후 Actions 탭에서 확인

# Exit Gate: 전체 검증
docker compose up -d
pytest                                # 전체 테스트
curl http://localhost:8000/health
curl http://localhost:3000             # Next.js 대시보드 접근
```

---

## 5) Exit Gate 체크리스트

- [ ] `docker compose up -d` → 전 컨테이너 기동
- [ ] `GET /health` → 200
- [ ] `GET /version` → 200
- [ ] `GET /docs` → Swagger UI
- [ ] `alembic upgrade head` → migration 성공
- [ ] Next.js 빈 대시보드 접근 가능
- [ ] CI 파이프라인 통과
