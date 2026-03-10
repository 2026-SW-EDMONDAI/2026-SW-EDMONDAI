# SegmentFlow MVP 이슈/마일스톤 설계 문서

## 범위

본 문서는 SegmentFlow의 MVP를 **5개 마일스톤(M1~M5)** 으로 나누고, 각 마일스톤별 목표, 핵심 산출물, 세부 이슈, 완료 기준을 정의한다.

---

# 1. MVP 목표 재정의

## MVP에서 반드시 검증해야 하는 것

1. 교육영상을 업로드하고 세그먼트를 생성할 수 있다.
2. 세그먼트 단위 학습 퍼널을 볼 수 있다.
3. 명시적 신호 + 암묵적 신호를 함께 해석할 수 있다.
4. Agent가 광고 위치를 추천할 수 있다.
5. 운영자가 추천을 검토, 수정, 승인할 수 있다.
6. 적용 후 광고 성과와 학습 가드레일을 함께 볼 수 있다.

## MVP 제외

* 개인화 추천
* 실시간 광고 입찰 최적화
* 자동 광고 집행
* 고급 실험 자동화
* 자유서술형 요약 평가 고도화

---

# 2. 마일스톤 개요

| 마일스톤 | 목표                    | 핵심 결과물                                  |
| ---- | --------------------- | --------------------------------------- |
| M1   | 프로젝트 골격 및 공통 기반 구축    | 레포, 인증, 공통 DB, 기본 UI shell, 배포 가능한 개발환경 |
| M2   | 교육영상 등록 및 세그먼트 생성     | 업로드, 자막 처리, 세그먼트 생성/조회/수정               |
| M3   | 학습 퍼널 수집·집계·시각화       | 이벤트 수집, 세그먼트 퍼널, 명시적/암묵적 신호 분석 화면       |
| M4   | Agent 추천 및 운영자 승인 플로우 | 추천 생성, 근거 표시, 승인/수정/적용                  |
| M5   | 성과 리포트, 가드레일, 안정화     | 성과 비교, 리포트, 운영 안정화, 파일럿 준비              |

---

# 3. 마일스톤 상세

---

# M1. 프로젝트 골격 및 공통 기반 구축

## 목적

팀이 병렬 개발할 수 있도록 **프론트/백엔드/워커/DB/인프라의 공통 기반**을 먼저 만든다.

## 산출물

* 모노레포 구조
* 로컬 개발환경
* 기본 인증/권한
* 핵심 DB 스키마 1차 반영
* 공통 레이아웃 UI
* CI/CD 초안
* 관측성 기본 설정

## 포함 범위

* Next.js 웹앱 초기화
* FastAPI 서버 초기화
* Celery worker 초기화
* PostgreSQL 연결
* RabbitMQ 연결
* Docker Compose 개발환경
* 로그인/조직 컨텍스트
* 공통 API 응답 포맷
* 기본 에러 핸들링
* 감사 로그 기본 구조

## M1 이슈

### M1-01. 모노레포 초기 구성

* `apps/web`, `apps/api`, `apps/worker`, `packages/*` 생성
* pnpm workspace 구성
* 공통 lint / format / env 템플릿 정리

### M1-02. Docker Compose 개발환경 구성

* postgres
* rabbitmq
* api
* worker
* web
* 볼륨/네트워크 설정

### M1-03. FastAPI 기본 앱 구성

* health check
* version endpoint
* 공통 exception handler
* request id middleware
* OpenAPI 문서 기본 세팅

### M1-04. Next.js 기본 앱 및 레이아웃 구성

* 로그인 화면
* 좌측 사이드바
* 상단 글로벌 바
* 빈 상태의 대시보드 shell

### M1-05. 인증/권한 모델 구현

* JWT 인증
* organization context
* admin/operator/analyst role guard

### M1-06. DB 마이그레이션 체계 구축

* Alembic 설정
* 초기 테이블 생성

  * organizations
  * users
  * organization_members
  * videos
  * guardrail_policies
  * audit_logs

### M1-07. 로깅/모니터링 기본 세팅

* OpenTelemetry SDK 연결
* API request latency metric
* worker task success/failure metric
* Grafana/Prometheus 로컬 기동

### M1-08. CI 기본 파이프라인

* lint
* type check
* backend unit test
* frontend build

## 완료 기준

* 개발자가 한 번의 명령으로 로컬 전체 스택을 올릴 수 있다.
* 로그인 후 빈 대시보드까지 진입 가능하다.
* 핵심 core 테이블 마이그레이션이 적용된다.
* API 문서가 자동 생성된다.
* 최소 health check와 CI가 통과한다.

## 선행 의존성

없음

## 리스크

* 초기에 레포 구조를 과하게 복잡하게 만들 위험
* 인증/조직 모델이 늦어지면 이후 API 전부가 흔들릴 수 있음

---

# M2. 교육영상 등록 및 세그먼트 생성

## 목적

MVP의 첫 핵심 기능인 **영상 등록 → 자막 연동 → 세그먼트 생성 → 검토/수정** 흐름을 완성한다.

## 산출물

* 신규 영상 등록 화면
* 영상 업로드 API
* 자막 업로드/조회
* 세그먼트 자동 생성 파이프라인
* 세그먼트 세트/버전 관리
* 세그먼트 수정, 분할, 병합
* 영상 상세 > 개요 / 세그먼트 탭

## 포함 범위

* video, asset, caption, segment 관련 테이블
* 영상 분석 job 실행
* 기본 세그먼트 생성 로직
* 세그먼트 검토 UI
* finalized / draft 상태 관리

## M2 이슈

### M2-01. 영상 등록 API 구현

* `POST /videos`
* 파일 업로드
* video_assets 저장
* signal config 초기값 저장

### M2-02. 자막 트랙 및 cue 저장

* caption_tracks / caption_cues 저장
* 기본 자막 조회 API 구현

### M2-03. 영상 상세/목록 API 구현

* 영상 목록
* 영상 상세
* 상태값 표시
* 최근 분석 시각 표시

### M2-04. 분석 작업 트리거 구현

* `POST /videos/{videoId}/analyze`
* Celery job enqueue
* 상태 변경: uploaded → processing

### M2-05. 세그먼트 자동 생성 워커 구현

* 자막 기반 분절
* 기본 title/topic 생성
* segment_set, segments 저장
* 분석 완료 처리

### M2-06. 세그먼트 세트 버전 관리 구현

* latest 조회
* clone
* finalize

### M2-07. 세그먼트 수정 API 구현

* 단건 수정
* 분할
* 병합
* draft 상태 검증

### M2-08. 세그먼트 검토 화면 구현

* 세그먼트 목록
* 세그먼트 상세 편집
* 분할/병합 버튼
* 확정 액션

### M2-09. 감사 로그 연결

* 영상 생성
* 분석 시작
* 세그먼트 수정
* finalize 이력 기록

## 완료 기준

* 운영자가 영상을 등록하고 분석을 실행할 수 있다.
* 분석 완료 후 세그먼트 목록을 확인할 수 있다.
* 세그먼트를 수정/분할/병합하고 확정할 수 있다.
* 영상 상세의 개요/세그먼트 탭이 동작한다.

## 선행 의존성

* M1 인증
* M1 DB/worker 기본 구조

## 리스크

* 세그먼트 생성 품질이 낮으면 이후 학습 퍼널과 추천 모두 영향받음
* 자막 품질 의존도가 높음

---

# M3. 학습 퍼널 수집·집계·시각화

## 목적

세그먼트 기반 제품의 핵심인 **학습 퍼널 분석**을 구현한다.
이 마일스톤에서 **명시적 신호 + 암묵적 신호 구조**가 실제 시스템에 반영된다.

## 산출물

* 플레이어 이벤트 수집 API
* learner session / learning events 저장
* 일배치 또는 주기 집계 작업
* segment metric snapshot 생성
* 학습 퍼널 화면
* 위험 구간 표시
* 명시적/암묵적 신호 구분 UI

## 포함 범위

* implicit events
* explicit events (MVP는 confidence check 중심)
* funnel API
* 영상 상세 > 학습 퍼널 탭
* 위험 플래그 계산

## M3 이슈

### M3-01. learner session 생성/관리

* anonymous session 생성 규칙
* player token 구조 정의
* 세션 종료 정책 정의

### M3-02. 이벤트 수집 API 구현

* `POST /player/events/batch`
* clientEventId 멱등 처리
* signalMode 검증
* eventType 검증

### M3-03. 이벤트 스키마/저장 구현

* learning_events 저장
* payload 저장
* implicit / explicit / ad 구분

### M3-04. 명시적 신호 구조 구현

* confidence check 이벤트 지원
* 값: understood / unsure / review_again
* explicit response rate 계산 준비

### M3-05. 집계 워커 구현

* raw events → segment_metric_snapshots 집계
* completion_rate
* dropout_rate
* rewatch_rate
* next_transition_rate
* explicit_response_rate
* confidence_* rate
* learning_stability_score

### M3-06. 위험 플래그 계산 로직

* dropout spike
* rewatch spike
* low explicit signal
* transition drop

### M3-07. 학습 퍼널 조회 API 구현

* `GET /videos/{videoId}/funnel`
* 세그먼트별 메트릭 + risk flags 반환

### M3-08. 학습 퍼널 화면 구현

* 타임라인
* 세그먼트 히트맵
* 퍼널 테이블
* explicit/implicit 필터 탭

### M3-09. 영상 개요 탭 KPI 연동

* 완주율
* 다음 세그먼트 이동률
* 이해도 체크 응답률

## 완료 기준

* 플레이어 이벤트가 적재된다.
* 세그먼트 단위 메트릭이 집계된다.
* 학습 퍼널 화면에서 위험 구간을 확인할 수 있다.
* 명시적/암묵적 신호를 분리해 볼 수 있다.

## 선행 의존성

* M2 세그먼트 구조 완료

## 리스크

* 이벤트 정의가 불안정하면 집계가 자꾸 깨짐
* raw event volume 증가 시 DB 성능 이슈 가능

---

# M4. Agent 추천 및 운영자 승인 플로우

## 목적

SegmentFlow의 차별점인 **Agent 광고 위치 추천**과 **사람 승인 기반 의사결정 흐름**을 완성한다.

## 산출물

* recommendation run 생성
* candidate 생성
* evidence 생성
* Agent 추천 화면
* 추천 검토/승인/수정/반려
* 실제 placement 생성

## 포함 범위

* recommendation tables
* evidence 로직
* candidate ranking
* review 및 apply 플로우
* 추천 관리 목록

## M4 이슈

### M4-01. 추천 입력 규격 정의

* 어떤 메트릭을 추천 엔진 입력으로 쓸지 확정
* 세그먼트 경계 후보 생성 기준 정의
* 가드레일 적용 순서 정의

### M4-02. 추천 실행 API 구현

* `POST /videos/{videoId}/recommendation-runs`
* 비동기 실행
* recommendation_run 상태 관리

### M4-03. 추천 후보 생성 로직 구현

* segment boundary candidate 생성
* 추천 제외 조건 적용
* rank 산정
* confidence score 계산

### M4-04. 근거 신호 생성 로직 구현

* implicit 근거
* explicit 근거
* exclusion 근거
* rationale summary 생성

### M4-05. 추천 후보 조회 API 구현

* run 상세
* candidate 목록
* evidence 포함 응답

### M4-06. Agent 추천 화면 구현

* 추천 Top N
* 추천 이유 카드
* 위험도
* 대안 슬롯
* 타임라인 표시

### M4-07. 추천 리뷰 액션 API 구현

* approve
* reject
* modify
* note

### M4-08. 추천 적용 API 구현

* approved/modifed candidate → placement 생성
* applied 상태 반영

### M4-09. 추천 관리 목록 화면 구현

* 대기/승인/반려 필터
* 위험도 필터
* 영상별 검토 진입

## 완료 기준

* 특정 영상에 대해 추천을 생성할 수 있다.
* 후보별 추천 근거를 볼 수 있다.
* 운영자가 승인/반려/수정할 수 있다.
* 실제 광고 위치 placement가 생성된다.

## 선행 의존성

* M3 학습 퍼널/지표 완료
* guardrail policy 기본값 존재

## 리스크

* 추천 품질이 낮으면 UI는 완성돼도 실사용성이 낮아짐
* 근거 설명이 약하면 운영자 신뢰를 얻기 어려움

---

# M5. 성과 리포트, 가드레일, 안정화

## 목적

추천 적용 이후 **광고 성과와 학습 품질을 같이 검증하는 루프**를 만들고, 파일럿 가능한 수준으로 안정화한다.

## 산출물

* placement performance 집계
* 영상 성과 리포트
* 가드레일 판정
* 감사 로그 화면
* 운영 안정화 작업
* MVP QA / 파일럿 준비

## 포함 범위

* 광고 이벤트와 placement 연결
* before/after 또는 baseline/treatment 비교
* guardrail warning
* 리포트 UI
* 로그 화면
* 성능/품질 안정화

## M5 이슈

### M5-01. placement 성과 집계 로직

* ad_impression / ad_click를 placement에 연결
* placement_performance_daily 집계

### M5-02. 영상 성과 비교 API 구현

* CTR 전후 비교
* completion/transition/explicit signal 비교
* candidate별 비교 결과 반환

### M5-03. 가드레일 판정 로직 구현

* completion drop threshold
* transition drop threshold
* explicit signal drop threshold
* overall guardrail status

### M5-04. 성과 리포트 화면 구현

* 적용 전/후 비교
* 가드레일 상태 배지
* candidate별 성과 비교

### M5-05. 감사 로그 화면 구현

* 추천 생성
* 승인
* 수정
* 적용
* 세그먼트 변경 이력 조회

### M5-06. 추천 품질/시스템 안정화

* API 응답 속도 점검
* worker retry 정책 정리
* queue backlog 모니터링
* DB 인덱스 보강

### M5-07. E2E 테스트 및 QA

* 영상 등록 → 분석 → 세그먼트 수정 → 퍼널 조회 → 추천 → 승인 → 적용 → 리포트
* 핵심 happy path 자동화

### M5-08. 파일럿 운영 체크리스트 작성

* 운영 가이드
* 이벤트 삽입 가이드
* 장애 대응 가이드
* KPI 측정 기준 정리

## 완료 기준

* 추천 적용 후 성과를 확인할 수 있다.
* 가드레일 위반 여부를 판단할 수 있다.
* 운영 로그가 남고 추적 가능하다.
* 핵심 사용자 시나리오가 E2E로 검증된다.
* 파일럿 배포 가능한 수준의 안정성이 확보된다.

## 선행 의존성

* M4 placement 생성 완료
* 광고 이벤트 수집 가능

## 리스크

* 비교군 정의가 불명확하면 리포트 설득력이 약해짐
* CTR과 학습 KPI를 함께 해석하는 기준이 모호할 수 있음

---

# 4. 마일스톤 간 의존성

```text
M1 → M2 → M3 → M4 → M5
```

좀 더 세부적으로 보면:

```text
M1 공통 기반
  ↓
M2 영상/세그먼트
  ↓
M3 이벤트/퍼널
  ↓
M4 추천/승인
  ↓
M5 성과/가드레일/안정화
```

### 병렬 가능 항목

* M2 후반부 세그먼트 UI와 M3 이벤트 적재 일부는 병렬 가능
* M3 후반부 퍼널 UI와 M4 추천 로직 일부는 병렬 가능
* M4 후반부 추천 화면과 M5 로그/리포트 일부는 병렬 가능

---

# 5. 우선순위 기준

## P0

없으면 MVP가 성립하지 않는 항목

* 영상 등록
* 세그먼트 생성/수정
* 이벤트 수집
* 학습 퍼널 조회
* 추천 생성
* 추천 승인/적용

## P1

MVP 품질과 실사용성을 높이는 항목

* 위험 플래그
* 추천 근거 상세
* 성과 리포트
* 가드레일 판정
* 로그 화면

## P2

파일럿 이후 또는 고도화 항목

* 한 줄 요약 신호
* 퀴즈 연동 고도화
* 세그먼트 자동 품질 평가
* 추천 품질 self-tuning

---

# 6. 마일스톤별 대표 이슈 수 요약

| 마일스톤 | 이슈 수 |
| ---- | ---: |
| M1   |    8 |
| M2   |    9 |
| M3   |    9 |
| M4   |    9 |
| M5   |    8 |

총 **43개 핵심 이슈**로 MVP를 설계한 셈입니다.

---

# 7. 실제 운영용 이슈 템플릿

실제로 Jira/Notion/Trello에 옮길 때는 아래 템플릿을 쓰면 좋습니다.

## 이슈 템플릿

**제목**
`[M3][API] 학습 퍼널 조회 API 구현`

**설명**

* 목적:
* 배경:
* 입력:
* 출력:
* 예외 케이스:
* 연관 API/테이블:
* 완료 조건:

**체크리스트**

* [ ] API route 구현
* [ ] service layer 구현
* [ ] DB query 구현
* [ ] unit test 작성
* [ ] Swagger 반영
* [ ] audit log 연결

**완료 기준**

* 정상 응답
* 예외 처리
* 테스트 통과
* 문서 반영

---

# 8. 최종 완료 정의 (MVP Definition of Done)

아래가 모두 충족되면 MVP 완료로 본다.

1. 운영자가 교육영상을 등록할 수 있다.
2. 시스템이 세그먼트를 생성하고 운영자가 수정할 수 있다.
3. 세그먼트 단위 학습 퍼널이 시각화된다.
4. 명시적 신호와 암묵적 신호가 함께 집계된다.
5. Agent가 광고 위치를 추천한다.
6. 운영자가 추천을 승인/수정/적용할 수 있다.
7. 적용 후 CTR과 학습 가드레일을 함께 볼 수 있다.
8. 핵심 플로우가 E2E 테스트로 검증된다.

---