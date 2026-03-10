# SegmentFlow Tech Stack v1

## 1. 기술 선택 원칙

SegmentFlow는 일반 웹서비스가 아니라,
**운영 대시보드 + 비동기 영상 분석 + 세그먼트 퍼널 집계 + Agent 추천**이 함께 돌아가는 구조다.
그래서 스택 선정 기준은 다음 4가지다.

1. **MVP 구현 속도**
2. **비동기 분석 파이프라인 대응력**
3. **운영자 대시보드 개발 생산성**
4. **이벤트 로그/집계/추천 결과를 한 흐름으로 연결할 수 있는 안정성**

또한 초기에는 과도한 분산 시스템보다, **단순하지만 확장 가능한 구조**를 우선한다.

---

## 2. 한눈에 보는 권장 스택

### Frontend

* **Next.js (App Router)**
* **TypeScript**
* **pnpm**
* **Playwright** (E2E)
* **React Query 또는 SWR 계열 데이터 패칭**
* **Charting Library**: Recharts 또는 ECharts 중 1개

Next.js는 App Router를 공식 지원하며, Node.js 서버나 Docker 컨테이너로 배포할 수 있다. 운영 대시보드처럼 서버 렌더링과 클라이언트 상호작용이 모두 필요한 경우에 잘 맞는다. ([Next.js][1])

### Backend

* **Python**
* **FastAPI**
* **Uvicorn**
* **Pydantic v2**
* **SQLAlchemy 2.0**

FastAPI는 Python type hints 기반의 고성능 API 프레임워크이며, async 처리와 BackgroundTasks를 공식적으로 제공한다. Uvicorn은 ASGI 서버이고, Pydantic은 데이터 검증, SQLAlchemy 2.0은 ORM/Core 양쪽을 다루는 표준적인 Python DB 툴킷으로 적합하다. ([FastAPI][2])

### Database / Storage

* **PostgreSQL**
* **Amazon S3** 또는 S3-compatible object storage

PostgreSQL은 `jsonb`와 GIN 인덱스를 지원해 세그먼트 메타데이터, 추천 근거, 이벤트 payload 같은 반정형 데이터를 다루기 좋다. S3는 객체 스토리지로 대용량 영상, 자막, 리포트 파일 저장에 적합하다. ([PostgreSQL][3])

### Async / Queue

* **Celery**
* **RabbitMQ** (권장 broker)

Celery는 분산 작업 큐로, 실시간 처리와 스케줄링을 지원한다. RabbitMQ는 Celery의 기본 broker이며, durable queue와 acknowledgements 기반의 신뢰성 있는 작업 분배에 적합하다. 교육영상 분석처럼 시간이 오래 걸리는 작업에는 Redis보다 RabbitMQ 쪽이 더 안전한 기본값이다. ([Celery Documentation][4])

### Infra / Deployment

* **Docker Compose** (local/dev)
* **AWS ECS Fargate** (prod 권장)
* **AWS ALB**
* **Amazon RDS for PostgreSQL**
* **CloudFront** (프론트/정적 자산 CDN)

Docker Compose는 멀티 컨테이너 앱을 정의·실행하기에 적합하고, Fargate는 서버나 EC2 클러스터를 직접 관리하지 않고 컨테이너를 실행할 수 있다. ALB는 트래픽의 단일 진입점 역할을 하며, RDS for PostgreSQL은 백업, 복구, Multi-AZ 같은 관리형 운영 기능을 제공한다. CloudFront는 정적/동적 콘텐츠를 글로벌 엣지로 빠르게 전달한다. ([Docker Documentation][5])

### Observability

* **OpenTelemetry**
* **Prometheus**
* **Alertmanager**
* **Grafana**

OpenTelemetry는 traces, metrics, logs를 다루는 벤더 중립 텔레메트리 프레임워크다. Prometheus는 모니터링/알림 툴킷, Alertmanager는 알림 중복 제거·그룹화·라우팅, Grafana는 대시보드 시각화에 적합하다. ([OpenTelemetry][6])

### Testing

* **pytest**
* **Playwright**

pytest는 fixture 기반 테스트 구성이 강하고, Playwright는 현대 웹앱용 E2E 테스트 프레임워크로 Chromium, Firefox, WebKit을 지원한다. ([pytest][7])

---

## 3. 최종 권장 조합

### 3.1 MVP 권장안

* Frontend: **Next.js + TypeScript + pnpm**
* Backend: **FastAPI + Uvicorn + Pydantic + SQLAlchemy**
* DB: **PostgreSQL**
* Queue: **Celery + RabbitMQ**
* File Storage: **S3**
* Local Dev: **Docker Compose**
* Observability: **OpenTelemetry + Prometheus + Grafana**
* Test: **pytest + Playwright**

이 조합의 장점은 **Python 중심 AI/분석 파이프라인**과 **운영 대시보드 개발 생산성**을 동시에 챙길 수 있다는 점이다. Next.js는 App Router와 Docker/Node 배포 경로가 명확하고, FastAPI는 async API와 Python 생태계 연동이 좋다. PostgreSQL은 운영 DB로 충분히 강력하고, 반정형 데이터 처리를 위한 `jsonb`도 지원한다. ([Next.js][1])

---

## 4. 레이어별 상세 스택

## 4.1 Frontend

### 선택

* **Next.js**
* **TypeScript**
* **pnpm**

### 이유

SegmentFlow는 일반 마케팅 사이트가 아니라,
대시보드·리스트·타임라인·세그먼트 상세·추천 검토 화면이 핵심이다.
그래서 CSR만으로 밀기보다, **라우팅 구조가 명확하고 서버 렌더링과 클라이언트 렌더링을 함께 쓰기 쉬운 프레임워크**가 적합하다. Next.js App Router는 이런 운영형 웹앱에 잘 맞고, 배포 옵션도 Node 서버와 Docker를 모두 지원한다. pnpm은 빠른 설치와 workspace 지원이 있어 프론트/백엔드 공용 모듈을 나눌 때 유리하다. ([Next.js][1])

### 역할

* 운영자 대시보드
* 영상 목록 / 상세
* 세그먼트 검토 UI
* 학습 퍼널 히트맵/타임라인
* Agent 추천 승인 화면
* 성과 리포트

### 비고

차트는 D3를 처음부터 직접 쓰기보다,
**Recharts 또는 ECharts 중 하나**로 가는 게 MVP 속도에 유리하다.
이건 공식 문서 기반 사실보다는 구현 전략 추천이다.

---

## 4.2 Backend API

### 선택

* **FastAPI**
* **Uvicorn**
* **Pydantic**
* **SQLAlchemy**

### 이유

SegmentFlow 백엔드는 다음 요구를 동시에 만족해야 한다.

* 운영자용 CRUD API
* 세그먼트/추천/리포트 조회 API
* 플레이어 이벤트 수집 API
* 비동기 분석 작업 트리거
* Python 기반 추천 로직/에이전트 연동

FastAPI는 type hints 기반 API 정의와 async 처리를 제공하고, BackgroundTasks도 지원한다. Uvicorn은 ASGI 서버이며, Pydantic은 요청/응답 스키마 검증에 적합하다. SQLAlchemy 2.0은 ORM과 Core를 모두 다룰 수 있어서 운영성 CRUD와 집계 쿼리를 함께 가져가기 좋다. ([FastAPI][2])

### 역할

* 인증/인가
* 영상 등록 API
* 세그먼트 수정 API
* 퍼널 조회 API
* 추천 생성/승인 API
* 리포트 API
* 이벤트 수집 API

---

## 4.3 Database

### 선택

* **PostgreSQL**

### 이유

이 프로젝트는 관계형 데이터와 반정형 데이터가 섞여 있다.

관계형:

* videos
* segments
* recommendation_runs
* placements
* reviews

반정형:

* key_concepts
* recommendation evidence
* event payload
* signal config

PostgreSQL은 `jsonb`와 GIN 인덱스를 지원하므로 이 조합에 잘 맞는다. 즉, SegmentFlow는 초기 MVP에서 굳이 별도 document DB를 추가하지 않아도 된다. ([PostgreSQL][3])

### 저장 대상

* 운영 데이터
* 세그먼트 버전
* 추천 후보 / 승인 이력
* 집계 스냅샷
* 감사 로그

### 권장 운영 방식

* **운영 DB는 PostgreSQL 1개로 시작**
* raw event는 같은 Postgres에 받아도 되지만, 장기적으로는 파티셔닝과 집계 배치를 반드시 둔다

---

## 4.4 Queue / Worker

### 선택

* **Celery**
* **RabbitMQ**

### 이유

영상 분석은 요청-응답 안에서 끝내면 안 된다.
세그먼트 생성, 자막 처리, 퍼널 재집계, 추천 생성은 모두 **비동기 잡**으로 돌아야 한다.

Celery는 task queue와 scheduling을 지원하고, RabbitMQ는 Celery의 기본 broker다. RabbitMQ는 durable queue, acknowledgements, reliable delivery 관련 가이드를 명확히 제공한다. SegmentFlow처럼 “처리 누락”이 민감한 서비스에서는 RabbitMQ가 기본값으로 더 적절하다. ([Celery Documentation][4])

### 큐 분리 권장

* `video-processing`
* `metrics-aggregation`
* `recommendation`
* `default`

Celery는 task routing과 여러 queue 구성을 지원하므로, 이 구조로 시작하는 것이 좋다. ([Celery Documentation][8])

---

## 4.5 File / Object Storage

### 선택

* **Amazon S3**

### 이유

교육영상 원본, 자막 파일, 생성 리포트는 파일 크기가 크고 DB에 넣기 적합하지 않다.
S3는 객체 스토리지이며, 객체와 메타데이터를 bucket 안에 저장하는 구조라 영상/자막 보관에 잘 맞는다. ([AWS Documentation][9])

### 저장 대상

* 원본 영상
* 자막 파일
* 분석 산출물 JSON
* CSV export
* 리포트 파일

---

## 4.6 Infra / Deployment

## Local / Dev

### 선택

* **Docker Compose**

### 이유

프론트, API, worker, broker, DB를 한 번에 띄워야 하므로 로컬에서는 Compose가 가장 단순하다. Compose는 멀티 컨테이너 애플리케이션 정의·실행용 도구다. ([Docker Documentation][5])

### 개발 환경 컨테이너

* `web` (Next.js)
* `api` (FastAPI)
* `worker` (Celery Worker)
* `beat` (optional)
* `rabbitmq`
* `postgres`
* `otel-collector` (optional)

---

## Production

### 선택

* **AWS ECS Fargate**
* **ALB**
* **RDS for PostgreSQL**
* **S3**
* **CloudFront**

### 이유

MVP~파일럿 단계에서는 Kubernetes보다 **운영 복잡도가 낮은 관리형 컨테이너 환경**이 더 낫다.
Fargate는 서버/클러스터를 직접 관리하지 않고 컨테이너를 실행할 수 있고, ALB는 단일 진입점으로 여러 대상에 트래픽을 분산한다. RDS for PostgreSQL은 백업, 복구, Multi-AZ, read replica 같은 운영 기능을 제공한다. CloudFront는 정적/동적 콘텐츠를 엣지에서 빠르게 전달한다. ([AWS Documentation][10])

### 권장 배포 구조

* CloudFront → Next.js
* ALB → FastAPI / Worker 내부 연동
* RDS PostgreSQL
* S3
* RabbitMQ (관리형 또는 별도 컨테이너)
* Prometheus / Grafana / Alertmanager

---

## 4.7 Observability

### 선택

* **OpenTelemetry**
* **Prometheus**
* **Alertmanager**
* **Grafana**

### 이유

SegmentFlow는 단순 API 모니터링만으로 부족하다.
다음 흐름을 봐야 한다.

* 영상 분석 job latency
* recommendation run 실패율
* event ingestion 성공률
* DB query 지연
* worker backlog
* guardrail 위반률

OpenTelemetry는 traces, metrics, logs를 다루는 공통 텔레메트리 프레임워크이고, Prometheus는 시계열 모니터링, Alertmanager는 알림 라우팅/중복 제거, Grafana는 대시보드 시각화에 적합하다. ([OpenTelemetry][6])

### 필수 대시보드

* API latency / error rate
* Celery queue length / worker success rate
* recommendation run success/failure
* event ingestion throughput
* PostgreSQL connection / slow query
* 가드레일 위반 영상 수

---

## 4.8 Testing

### 선택

* **pytest**
* **Playwright**

### 이유

백엔드는 fixture 기반으로 DB, API, mock broker를 안정적으로 구성하는 게 중요하고, 프론트는 운영자 승인 플로우 전체를 브라우저 레벨에서 검증해야 한다. pytest는 fixture 시스템이 강하고, Playwright는 브라우저 엔진 전반에 걸친 E2E 테스트를 지원한다. ([pytest][7])

### 테스트 범위

* API contract tests
* segment edit flow tests
* recommendation approval flow tests
* event ingestion validation tests
* report rendering E2E tests

---

# 5. 권장 아키텍처 맵

```text
[ Next.js Dashboard ]
        ↓
      ALB
        ↓
[ FastAPI API ]
   ├─ PostgreSQL
   ├─ S3
   ├─ RabbitMQ
   └─ OpenTelemetry
        ↓
[ Celery Workers ]
   ├─ video processing
   ├─ metrics aggregation
   └─ recommendation generation
```

이 구조는 **운영용 웹앱**, **비동기 분석**, **추천 파이프라인**을 깔끔하게 분리한다.

---

# 6. MVP 기준 폴더/레포 전략

## 추천

**Monorepo**

```text
/apps
  /web        -> Next.js
  /api        -> FastAPI
  /worker     -> Celery worker
/packages
  /schemas    -> API DTO, typed contracts
  /ui         -> 공통 UI 컴포넌트
  /config     -> lint / tsconfig / env templates
/infrastructure
  /docker
  /terraform or aws
```

pnpm은 workspace 지원이 있고, 프론트 쪽 패키지 관리를 빠르게 가져갈 수 있어서 monorepo에 잘 맞는다. ([pnpm][11])

---

# 7. 지금 단계에서 채택하지 않는 스택

초기에는 아래를 **의도적으로 미채택**하는 게 좋습니다.

## Kubernetes

파일럿 전 단계에서는 과합니다.
Fargate/ECS로 충분합니다. ([AWS Documentation][10])

## 별도 NoSQL DB

PostgreSQL `jsonb`로 충분히 시작 가능합니다. ([PostgreSQL][3])

## 별도 실시간 스트리밍 플랫폼

Kafka 같은 스트리밍 플랫폼은 이벤트 트래픽이 아주 커진 뒤 검토해도 늦지 않습니다.
MVP는 배치 이벤트 수집 + 집계 구조로 충분합니다.
이건 설계 추천입니다.

## Vector DB

현재 PRD 범위에서는 필수 아님.
추천은 세그먼트 지표 + 규칙 + LLM 설명 생성으로 충분합니다.
이것도 설계 추천입니다.

---

# 8. 최종 권장안 요약

### 가장 추천하는 스택

* **Frontend:** Next.js + TypeScript + pnpm
* **Backend:** FastAPI + Uvicorn + Pydantic + SQLAlchemy
* **DB:** PostgreSQL
* **Queue:** Celery + RabbitMQ
* **Storage:** S3
* **Infra:** Docker Compose → ECS Fargate + ALB + RDS + CloudFront
* **Observability:** OpenTelemetry + Prometheus + Alertmanager + Grafana
* **Testing:** pytest + Playwright

### 한 줄 정리

이 조합은 **교육영상 분석처럼 Python 친화적 백엔드**와 **운영 대시보드 중심 웹앱**을 가장 균형 있게 묶는 구성입니다. Next.js와 FastAPI는 각각 대시보드와 API에 잘 맞고, Celery+RabbitMQ는 분석 파이프라인을 비동기로 분리하기 좋으며, PostgreSQL은 관계형 + 반정형 데이터를 함께 다루기에 적합합니다. ([Next.js][1])


[1]: https://nextjs.org/docs?utm_source=chatgpt.com "Next.js Docs"
[2]: https://fastapi.tiangolo.com/?utm_source=chatgpt.com "FastAPI"
[3]: https://www.postgresql.org/docs/current/datatype-json.html?utm_source=chatgpt.com "Documentation: 18: 8.14. JSON Types"
[4]: https://docs.celeryq.dev/?utm_source=chatgpt.com "Celery - Distributed Task Queue — Celery 5.6.2 documentation"
[5]: https://docs.docker.com/compose/?utm_source=chatgpt.com "Docker Compose"
[6]: https://opentelemetry.io/docs/?utm_source=chatgpt.com "Documentation"
[7]: https://docs.pytest.org/?utm_source=chatgpt.com "pytest documentation"
[8]: https://docs.celeryq.dev/en/main/userguide/configuration.html?utm_source=chatgpt.com "Configuration and defaults — Celery 5.6.2 documentation"
[9]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html?utm_source=chatgpt.com "What is Amazon S3? - Amazon Simple Storage Service"
[10]: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html?utm_source=chatgpt.com "Architect for AWS Fargate for Amazon ECS"
[11]: https://pnpm.io/?utm_source=chatgpt.com "Fast, disk space efficient package manager | pnpm"
