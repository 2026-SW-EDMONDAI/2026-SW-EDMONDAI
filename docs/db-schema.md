# SegmentFlow DB 스키마 v1

## 0. 설계 원칙

### 0.1 핵심 설계 원칙

1. **세그먼트는 버전 관리한다**
   세그먼트 자동 생성 후 사람이 수정할 수 있으므로, `segment_set` 버전을 둔다.

2. **학습 신호는 명시적/암묵적 신호를 하나의 이벤트 모델로 저장한다**
   단, `signal_mode`로 구분한다.

3. **원시 이벤트와 집계 지표를 분리한다**
   `learning_events`는 원시 로그, `segment_metric_snapshots`는 운영 화면용 집계다.

4. **추천 결과도 버전 관리한다**
   추천 생성 시점의 세그먼트/지표 기준이 남아야 하므로 `recommendation_run` 단위로 관리한다.

5. **사람 승인 이력을 별도 저장한다**
   추천이 아니라 “최종 의사결정”이 중요하므로 review / placement 테이블이 필요하다.

---

# 1. 전체 ERD 개요

```text
organizations
 └─ organization_members ─ users

organizations
 └─ videos
     ├─ video_assets
     ├─ caption_tracks
     │   └─ caption_cues
     ├─ video_signal_configs
     ├─ segment_sets
     │   └─ segments
     ├─ learner_sessions
     │   └─ learning_events
     ├─ segment_metric_snapshots
     ├─ recommendation_runs
     │   └─ recommendation_candidates
     │       ├─ recommendation_evidence
     │       └─ recommendation_reviews
     └─ ad_placements
         └─ placement_performance_daily

organizations
 └─ guardrail_policies

audit_logs
```

---

# 2. 권장 타입 / 공통 규칙

## 2.1 기본 규칙

* Core 테이블 PK: `UUID`
* 이벤트 테이블 PK: `BIGSERIAL` 또는 `UUID + partition`
* 시간: `TIMESTAMPTZ`
* 영상 위치: `INT` (`ms` 단위)
* 유연한 데이터: `JSONB`
* 상태값: PostgreSQL `ENUM` 또는 `TEXT + CHECK`

## 2.2 공통 컬럼

대부분의 운영 테이블에 아래 컬럼 포함 추천:

* `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
* `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`
* `deleted_at TIMESTAMPTZ NULL` (soft delete 필요 시)

---

# 3. Enum 정의

## 3.1 `video_status`

* `draft`
* `uploaded`
* `processing`
* `analyzed`
* `failed`
* `archived`

## 3.2 `segment_set_status`

* `draft`
* `finalized`
* `archived`

## 3.3 `signal_mode`

* `implicit`
* `explicit`
* `ad`

## 3.4 `event_type`

* `video_start`
* `segment_start`
* `segment_complete`
* `pause`
* `seek_back`
* `rewatch`
* `speed_change`
* `subtitle_toggle`
* `next_segment_start`
* `exit`
* `confidence_check_submit`
* `quiz_submit`
* `concept_select`
* `summary_submit`
* `ad_impression`
* `ad_click`

## 3.5 `recommendation_run_status`

* `queued`
* `running`
* `succeeded`
* `failed`

## 3.6 `candidate_status`

* `proposed`
* `approved`
* `rejected`
* `modified`
* `applied`

## 3.7 `risk_level`

* `low`
* `medium`
* `high`

## 3.8 `review_action`

* `approve`
* `reject`
* `modify`
* `note`

## 3.9 `placement_status`

* `pending`
* `applied`
* `reverted`

---

# 4. Core Schema

## 4.1 `organizations`

조직/워크스페이스 단위

| 컬럼         | 타입                 | 설명     |
| ---------- | ------------------ | ------ |
| id         | UUID PK            | 조직 ID  |
| name       | VARCHAR(120)       | 조직명    |
| slug       | VARCHAR(80) UNIQUE | 조직 식별자 |
| created_at | TIMESTAMPTZ        | 생성시각   |
| updated_at | TIMESTAMPTZ        | 수정시각   |

---

## 4.2 `users`

운영자 계정

| 컬럼         | 타입                  | 설명        |
| ---------- | ------------------- | --------- |
| id         | UUID PK             | 사용자 ID    |
| email      | VARCHAR(255) UNIQUE | 이메일       |
| name       | VARCHAR(120)        | 이름        |
| role       | VARCHAR(40)         | 시스템 기본 역할 |
| created_at | TIMESTAMPTZ         | 생성시각      |
| updated_at | TIMESTAMPTZ         | 수정시각      |

---

## 4.3 `organization_members`

조직별 사용자 권한

| 컬럼              | 타입          | 설명                         |
| --------------- | ----------- | -------------------------- |
| id              | UUID PK     | 멤버십 ID                     |
| organization_id | UUID FK     | organizations.id           |
| user_id         | UUID FK     | users.id                   |
| org_role        | VARCHAR(40) | admin / operator / analyst |
| created_at      | TIMESTAMPTZ | 생성시각                       |

**Unique**

* `(organization_id, user_id)`

---

## 4.4 `videos`

교육영상 기본 정보

| 컬럼              | 타입               | 설명                    |
| --------------- | ---------------- | --------------------- |
| id              | UUID PK          | 영상 ID                 |
| organization_id | UUID FK          | organizations.id      |
| title           | VARCHAR(255)     | 영상명                   |
| description     | TEXT             | 설명                    |
| status          | video_status     | 상태                    |
| duration_ms     | INT              | 전체 길이(ms)             |
| source_type     | VARCHAR(30)      | upload / external_url |
| source_url      | TEXT NULL        | 외부 URL                |
| uploaded_by     | UUID FK          | users.id              |
| analyzed_at     | TIMESTAMPTZ NULL | 최근 분석 완료 시각           |
| created_at      | TIMESTAMPTZ      | 생성시각                  |
| updated_at      | TIMESTAMPTZ      | 수정시각                  |

**Index**

* `(organization_id, status)`
* `(organization_id, created_at DESC)`

---

## 4.5 `video_assets`

영상/자막 원본 파일

| 컬럼              | 타입           | 설명                                       |
| --------------- | ------------ | ---------------------------------------- |
| id              | UUID PK      | 자산 ID                                    |
| video_id        | UUID FK      | videos.id                                |
| asset_type      | VARCHAR(30)  | video_file / subtitle_file / report_file |
| storage_path    | TEXT         | object storage path                      |
| file_name       | VARCHAR(255) | 파일명                                      |
| mime_type       | VARCHAR(100) | MIME type                                |
| file_size_bytes | BIGINT       | 파일 크기                                    |
| created_at      | TIMESTAMPTZ  | 생성시각                                     |

**Index**

* `(video_id, asset_type)`

---

## 4.6 `caption_tracks`

자막 트랙

| 컬럼            | 타입          | 설명                   |
| ------------- | ----------- | -------------------- |
| id            | UUID PK     | 자막 트랙 ID             |
| video_id      | UUID FK     | videos.id            |
| language_code | VARCHAR(10) | ko, en 등             |
| source        | VARCHAR(30) | uploaded / generated |
| is_default    | BOOLEAN     | 기본 자막 여부             |
| created_at    | TIMESTAMPTZ | 생성시각                 |

---

## 4.7 `caption_cues`

자막 구간 단위 데이터

| 컬럼               | 타입          | 설명                |
| ---------------- | ----------- | ----------------- |
| id               | UUID PK     | cue ID            |
| caption_track_id | UUID FK     | caption_tracks.id |
| seq_no           | INT         | 순서                |
| start_ms         | INT         | 시작 시각             |
| end_ms           | INT         | 종료 시각             |
| text             | TEXT        | 자막 텍스트            |
| created_at       | TIMESTAMPTZ | 생성시각              |

**Unique**

* `(caption_track_id, seq_no)`

**Index**

* `(caption_track_id, start_ms)`

---

## 4.8 `segment_sets`

세그먼트 버전 묶음

| 컬럼         | 타입                 | 설명                         |
| ---------- | ------------------ | -------------------------- |
| id         | UUID PK            | 세그먼트 세트 ID                 |
| video_id   | UUID FK            | videos.id                  |
| version_no | INT                | 버전 번호                      |
| status     | segment_set_status | draft / finalized          |
| created_by | UUID FK NULL       | users.id, auto면 null 허용 가능 |
| source     | VARCHAR(30)        | auto / manual / hybrid     |
| notes      | TEXT NULL          | 수정 메모                      |
| created_at | TIMESTAMPTZ        | 생성시각                       |
| updated_at | TIMESTAMPTZ        | 수정시각                       |

**Unique**

* `(video_id, version_no)`

---

## 4.9 `segments`

실제 세그먼트

| 컬럼             | 타입                | 설명              |
| -------------- | ----------------- | --------------- |
| id             | UUID PK           | 세그먼트 ID         |
| segment_set_id | UUID FK           | segment_sets.id |
| seq_no         | INT               | 세그먼트 순번         |
| start_ms       | INT               | 시작 시각           |
| end_ms         | INT               | 종료 시각           |
| title          | VARCHAR(255)      | 세그먼트 제목         |
| topic          | VARCHAR(255) NULL | 주제              |
| key_concepts   | JSONB NULL        | 핵심 개념 배열        |
| summary        | TEXT NULL         | 요약              |
| source_type    | VARCHAR(20)       | auto / edited   |
| created_at     | TIMESTAMPTZ       | 생성시각            |
| updated_at     | TIMESTAMPTZ       | 수정시각            |

**Unique**

* `(segment_set_id, seq_no)`

**Check**

* `start_ms < end_ms`

**Index**

* `(segment_set_id, start_ms)`

---

## 4.10 `video_signal_configs`

영상별 명시적 신호 설정

| 컬럼                       | 타입             | 설명             |
| ------------------------ | -------------- | -------------- |
| id                       | UUID PK        | 설정 ID          |
| video_id                 | UUID FK UNIQUE | videos.id      |
| confidence_check_enabled | BOOLEAN        | 이해도 체크 사용 여부   |
| quiz_enabled             | BOOLEAN        | 퀴즈 사용 여부       |
| concept_select_enabled   | BOOLEAN        | 핵심 개념 선택 사용 여부 |
| summary_enabled          | BOOLEAN        | 한 줄 요약 사용 여부   |
| config_json              | JSONB NULL     | 추가 설정          |
| created_at               | TIMESTAMPTZ    | 생성시각           |
| updated_at               | TIMESTAMPTZ    | 수정시각           |

---

## 4.11 `guardrail_policies`

조직 단위 가드레일 정책

| 컬럼                            | 타입           | 설명                 |
| ----------------------------- | ------------ | ------------------ |
| id                            | UUID PK      | 정책 ID              |
| organization_id               | UUID FK      | organizations.id   |
| name                          | VARCHAR(120) | 정책명                |
| completion_drop_limit_pp      | NUMERIC(5,2) | 완주율 허용 하락폭         |
| transition_drop_limit_pp      | NUMERIC(5,2) | 다음 세그먼트 이동률 허용 하락폭 |
| explicit_signal_drop_limit_pp | NUMERIC(5,2) | 명시적 신호 허용 하락폭      |
| min_confidence_score          | NUMERIC(5,2) | 최소 추천 신뢰도          |
| is_active                     | BOOLEAN      | 활성 정책 여부           |
| created_at                    | TIMESTAMPTZ  | 생성시각               |
| updated_at                    | TIMESTAMPTZ  | 수정시각               |

**Index**

* `(organization_id, is_active)`

---

# 5. Analytics Schema

## 5.1 `learner_sessions`

익명 학습 세션 단위

| 컬럼                 | 타입               | 설명                        |
| ------------------ | ---------------- | ------------------------- |
| id                 | UUID PK          | 세션 ID                     |
| video_id           | UUID FK          | videos.id                 |
| anonymous_user_key | VARCHAR(128)     | 익명/가명 사용자 키               |
| session_started_at | TIMESTAMPTZ      | 세션 시작                     |
| session_ended_at   | TIMESTAMPTZ NULL | 세션 종료                     |
| device_type        | VARCHAR(30) NULL | mobile / desktop / tablet |
| platform           | VARCHAR(30) NULL | web / app                 |
| country_code       | VARCHAR(5) NULL  | 국가코드                      |
| created_at         | TIMESTAMPTZ      | 생성시각                      |

**Index**

* `(video_id, session_started_at DESC)`
* `(anonymous_user_key)`

---

## 5.2 `learning_events`

명시적/암묵적/광고 이벤트 원시 로그

> 이 테이블은 트래픽이 많으므로 **월 단위 파티셔닝** 권장

| 컬럼                 | 타입                        | 설명                                    |
| ------------------ | ------------------------- | ------------------------------------- |
| id                 | BIGSERIAL PK              | 이벤트 ID                                |
| organization_id    | UUID FK                   | organizations.id                      |
| video_id           | UUID FK                   | videos.id                             |
| segment_set_id     | UUID FK NULL              | 세그먼트 세트 버전                            |
| segment_id         | UUID FK NULL              | 세그먼트 ID                               |
| learner_session_id | UUID FK                   | learner_sessions.id                   |
| signal_mode        | signal_mode               | implicit / explicit / ad              |
| event_type         | event_type                | 이벤트명                                  |
| event_value        | VARCHAR(100) NULL         | 예: understood / unsure / review_again |
| position_ms        | INT NULL                  | 이벤트 발생 시점                             |
| payload            | JSONB NULL                | 부가 정보                                 |
| occurred_at        | TIMESTAMPTZ               | 실제 발생 시각                              |
| received_at        | TIMESTAMPTZ DEFAULT now() | 서버 수신 시각                              |

### `payload` 예시

* `speed_change`: `{"from":1.0,"to":0.8}`
* `concept_select`: `{"selected":["A","B"]}`
* `summary_submit`: `{"text":"..."}`
* `ad_impression`: `{"ad_slot_id":"...", "creative_id":"..."}`

**Index**

* `(video_id, occurred_at DESC)`
* `(segment_id, event_type, occurred_at DESC)`
* `(learner_session_id, occurred_at)`
* `(signal_mode, event_type)`

---

## 5.3 `segment_metric_snapshots`

세그먼트 집계 지표

운영 화면에서 바로 쓰는 테이블.
원시 이벤트를 배치 집계해 만든다.

| 컬럼                           | 타입                | 설명                         |
| ---------------------------- | ----------------- | -------------------------- |
| id                           | UUID PK           | 스냅샷 ID                     |
| video_id                     | UUID FK           | videos.id                  |
| segment_set_id               | UUID FK           | segment_sets.id            |
| segment_id                   | UUID FK           | segments.id                |
| metric_date                  | DATE              | 집계 기준일                     |
| cohort_type                  | VARCHAR(30)       | all / baseline / treatment |
| placement_id                 | UUID FK NULL      | ad_placements.id           |
| viewers_started              | INT               | 진입 사용자 수                   |
| viewers_completed            | INT               | 완료 사용자 수                   |
| completion_rate              | NUMERIC(5,4)      | 완료율                        |
| dropout_rate                 | NUMERIC(5,4)      | 이탈률                        |
| rewatch_rate                 | NUMERIC(5,4)      | 재시청률                       |
| next_transition_rate         | NUMERIC(5,4)      | 다음 세그먼트 이동률                |
| avg_pause_count              | NUMERIC(8,2)      | 평균 pause 수                 |
| avg_seek_back_count          | NUMERIC(8,2)      | 평균 되감기 수                   |
| avg_speed_change_count       | NUMERIC(8,2)      | 평균 배속 변경 수                 |
| explicit_response_rate       | NUMERIC(5,4)      | 명시적 신호 응답률                 |
| confidence_positive_rate     | NUMERIC(5,4) NULL | 이해함 비율                     |
| confidence_unsure_rate       | NUMERIC(5,4) NULL | 애매함 비율                     |
| confidence_review_again_rate | NUMERIC(5,4) NULL | 다시보기 비율                    |
| learning_stability_score     | NUMERIC(6,3) NULL | 통합 안정성 점수                  |
| created_at                   | TIMESTAMPTZ       | 생성시각                       |

**Unique**

* `(segment_id, metric_date, cohort_type, placement_id)`

**Index**

* `(video_id, metric_date DESC)`
* `(segment_id, metric_date DESC)`

---

## 5.4 `video_metric_snapshots`

영상 전체 요약 지표

| 컬럼                     | 타입                | 설명                         |
| ---------------------- | ----------------- | -------------------------- |
| id                     | UUID PK           | 스냅샷 ID                     |
| video_id               | UUID FK           | videos.id                  |
| metric_date            | DATE              | 기준일                        |
| cohort_type            | VARCHAR(30)       | all / baseline / treatment |
| placement_id           | UUID FK NULL      | ad_placements.id           |
| total_viewers          | INT               | 총 시청자 수                    |
| completion_rate        | NUMERIC(5,4)      | 영상 완주율                     |
| avg_watch_rate         | NUMERIC(5,4)      | 평균 시청률                     |
| avg_watch_time_sec     | NUMERIC(10,2)     | 평균 시청 시간                   |
| next_transition_rate   | NUMERIC(5,4) NULL | 세그먼트 기반 전체 이동률             |
| explicit_response_rate | NUMERIC(5,4) NULL | 명시적 응답률                    |
| created_at             | TIMESTAMPTZ       | 생성시각                       |

---

# 6. Recommendation Schema

## 6.1 `recommendation_runs`

추천 생성 실행 단위

| 컬럼                  | 타입                        | 설명                         |
| ------------------- | ------------------------- | -------------------------- |
| id                  | UUID PK                   | 추천 실행 ID                   |
| video_id            | UUID FK                   | videos.id                  |
| segment_set_id      | UUID FK                   | segment_sets.id            |
| guardrail_policy_id | UUID FK                   | guardrail_policies.id      |
| status              | recommendation_run_status | 상태                         |
| triggered_by        | UUID FK NULL              | users.id, system이면 null 가능 |
| model_version       | VARCHAR(80) NULL          | 추천 로직 버전                   |
| input_snapshot_date | DATE NULL                 | 사용한 지표 기준일                 |
| input_summary       | JSONB NULL                | 주요 입력 요약                   |
| created_at          | TIMESTAMPTZ               | 생성시각                       |
| completed_at        | TIMESTAMPTZ NULL          | 완료 시각                      |

**Index**

* `(video_id, created_at DESC)`
* `(status, created_at DESC)`

---

## 6.2 `recommendation_candidates`

추천 광고 위치 후보

| 컬럼                         | 타입                | 설명                             |
| -------------------------- | ----------------- | ------------------------------ |
| id                         | UUID PK           | 후보 ID                          |
| recommendation_run_id      | UUID FK           | recommendation_runs.id         |
| video_id                   | UUID FK           | videos.id                      |
| segment_id                 | UUID FK           | segments.id                    |
| placement_type             | VARCHAR(30)       | after_segment / before_segment |
| placement_time_ms          | INT               | 추천 위치(ms)                      |
| rank_no                    | INT               | 추천 순위                          |
| confidence_score           | NUMERIC(5,4)      | 신뢰도                            |
| risk_level                 | risk_level        | low / medium / high            |
| expected_ctr_lift          | NUMERIC(6,4) NULL | 예상 CTR 개선폭                     |
| expected_completion_impact | NUMERIC(6,4) NULL | 예상 완주율 영향                      |
| expected_transition_impact | NUMERIC(6,4) NULL | 예상 이동률 영향                      |
| status                     | candidate_status  | 제안/승인/수정 등                     |
| rationale_summary          | TEXT              | 추천 요약 설명                       |
| created_at                 | TIMESTAMPTZ       | 생성시각                           |
| updated_at                 | TIMESTAMPTZ       | 수정시각                           |

**Unique**

* `(recommendation_run_id, rank_no)`

**Index**

* `(video_id, status)`
* `(segment_id)`

---

## 6.3 `recommendation_evidence`

추천 근거 신호

추천 이유 카드에 바로 쓰는 테이블

| 컬럼                  | 타입                 | 설명                                           |
| ------------------- | ------------------ | -------------------------------------------- |
| id                  | UUID PK            | 근거 ID                                        |
| candidate_id        | UUID FK            | recommendation_candidates.id                 |
| signal_mode         | signal_mode        | implicit / explicit / ad                     |
| signal_name         | VARCHAR(80)        | 예: completion_rate, confidence_positive_rate |
| signal_value        | NUMERIC(10,4) NULL | 수치값                                          |
| contribution_weight | NUMERIC(6,4) NULL  | 기여도                                          |
| direction           | VARCHAR(20)        | positive / negative / exclusion              |
| message             | TEXT               | 사람이 읽을 설명                                    |
| created_at          | TIMESTAMPTZ        | 생성시각                                         |

**Index**

* `(candidate_id, signal_mode)`

---

## 6.4 `recommendation_reviews`

운영자 승인/반려/수정 이력

| 컬럼                         | 타입            | 설명                               |
| -------------------------- | ------------- | -------------------------------- |
| id                         | UUID PK       | 리뷰 ID                            |
| candidate_id               | UUID FK       | recommendation_candidates.id     |
| reviewer_id                | UUID FK       | users.id                         |
| action                     | review_action | approve / reject / modify / note |
| original_placement_time_ms | INT NULL      | 원래 위치                            |
| modified_placement_time_ms | INT NULL      | 수정 위치                            |
| comment                    | TEXT NULL     | 메모                               |
| created_at                 | TIMESTAMPTZ   | 생성시각                             |

**Index**

* `(candidate_id, created_at DESC)`
* `(reviewer_id, created_at DESC)`

---

## 6.5 `ad_placements`

실제 적용된 광고 위치

추천과 실제 적용을 분리해서 저장

| 컬럼                | 타입               | 설명                           |
| ----------------- | ---------------- | ---------------------------- |
| id                | UUID PK          | placement ID                 |
| video_id          | UUID FK          | videos.id                    |
| candidate_id      | UUID FK NULL     | recommendation_candidates.id |
| segment_id        | UUID FK          | segments.id                  |
| applied_by        | UUID FK NULL     | users.id                     |
| placement_time_ms | INT              | 실제 적용 위치                     |
| status            | placement_status | pending / applied / reverted |
| applied_at        | TIMESTAMPTZ NULL | 적용 시각                        |
| reverted_at       | TIMESTAMPTZ NULL | 롤백 시각                        |
| notes             | TEXT NULL        | 메모                           |
| created_at        | TIMESTAMPTZ      | 생성시각                         |

**Index**

* `(video_id, status)`
* `(candidate_id)`

---

## 6.6 `placement_performance_daily`

광고 적용 후 성과 일별 스냅샷

| 컬럼                             | 타입                 | 설명               |
| ------------------------------ | ------------------ | ---------------- |
| id                             | UUID PK            | 성과 ID            |
| placement_id                   | UUID FK            | ad_placements.id |
| metric_date                    | DATE               | 기준일              |
| impressions                    | INT                | 광고 노출 수          |
| clicks                         | INT                | 클릭 수             |
| ctr                            | NUMERIC(5,4)       | 클릭률              |
| revenue                        | NUMERIC(12,2) NULL | 광고 수익            |
| exposed_viewers                | INT                | 광고 노출된 시청자 수     |
| exposed_completion_rate        | NUMERIC(5,4) NULL  | 노출 집단 완주율        |
| exposed_transition_rate        | NUMERIC(5,4) NULL  | 노출 집단 이동률        |
| exposed_explicit_response_rate | NUMERIC(5,4) NULL  | 노출 집단 명시적 응답률    |
| created_at                     | TIMESTAMPTZ        | 생성시각             |

**Unique**

* `(placement_id, metric_date)`

---

# 7. Audit / Log Schema

## 7.1 `audit_logs`

로그 탭 / 운영 추적용

| 컬럼              | 타입           | 설명                                                  |
| --------------- | ------------ | --------------------------------------------------- |
| id              | UUID PK      | 로그 ID                                               |
| organization_id | UUID FK      | organizations.id                                    |
| user_id         | UUID FK NULL | users.id, system이면 null                             |
| entity_type     | VARCHAR(40)  | video / segment_set / recommendation / placement    |
| entity_id       | UUID         | 대상 ID                                               |
| action          | VARCHAR(60)  | created / updated / approved / rejected / reapplied |
| message         | TEXT         | 로그 메시지                                              |
| metadata        | JSONB NULL   | 부가 정보                                               |
| created_at      | TIMESTAMPTZ  | 생성시각                                                |

**Index**

* `(entity_type, entity_id, created_at DESC)`
* `(organization_id, created_at DESC)`

---

# 8. MVP에서 반드시 필요한 최소 테이블

정말 MVP만 본다면 아래 테이블은 꼭 필요합니다.

## Core

* `organizations`
* `users`
* `organization_members`
* `videos`
* `video_assets`
* `caption_tracks`
* `caption_cues`
* `segment_sets`
* `segments`
* `video_signal_configs`
* `guardrail_policies`

## Analytics

* `learner_sessions`
* `learning_events`
* `segment_metric_snapshots`

## Recommendation

* `recommendation_runs`
* `recommendation_candidates`
* `recommendation_evidence`
* `recommendation_reviews`
* `ad_placements`

## Logging

* `audit_logs`

`video_metric_snapshots`, `placement_performance_daily`는 파일럿부터 붙이면 좋습니다.

---

# 9. 핵심 관계 설명

## 9.1 왜 `segment_set`이 필요한가

세그먼트가 자동 생성된 뒤 운영자가 수정하면 과거 지표와 추천이 달라질 수 있습니다.
그래서:

* `videos` 1:N `segment_sets`
* `segment_sets` 1:N `segments`

로 버전 관리해야 합니다.

---

## 9.2 왜 `learning_events`와 `segment_metric_snapshots`를 분리하나

운영 화면은 빠르게 떠야 하고, 이벤트는 매우 많습니다.

그래서:

* `learning_events`: 원시 로그 저장
* `segment_metric_snapshots`: 대시보드용 집계

로 분리합니다.

---

## 9.3 왜 `recommendation_candidate`와 `ad_placement`를 분리하나

추천은 “제안”이고, 실제 적용은 “결정”입니다.

예를 들어:

* Agent는 `S3 이후` 추천
* 운영자는 5초 뒤로 수정 후 적용

이 흐름을 남기려면 둘을 분리해야 합니다.

---

# 10. 인덱스 / 성능 포인트

## 10.1 꼭 필요한 인덱스

* `videos (organization_id, status)`
* `segments (segment_set_id, seq_no)`
* `learning_events (video_id, occurred_at DESC)`
* `learning_events (segment_id, event_type, occurred_at DESC)`
* `segment_metric_snapshots (segment_id, metric_date DESC)`
* `recommendation_runs (video_id, created_at DESC)`
* `recommendation_candidates (recommendation_run_id, rank_no)`
* `recommendation_reviews (candidate_id, created_at DESC)`

## 10.2 파티셔닝 권장

`learning_events`는 꼭 시간 기준 파티셔닝 권장:

* 월 단위 파티션
* 또는 주 단위 파티션

---

# 11. 추천 쿼리 기준으로 본 스키마 검증

이 스키마로 아래 질문에 대응 가능합니다.

### 1. 영상 상세 > 세그먼트 탭

* 특정 영상의 최신 `segment_set`
* 해당 `segments` 목록 조회

### 2. 학습 퍼널 탭

* `segment_metric_snapshots`에서 세그먼트별 완료율/이탈률/재시청률/명시적 반응률 조회

### 3. Agent 추천 탭

* 최신 `recommendation_run`
* 해당 `recommendation_candidates`
* 각 후보의 `recommendation_evidence`
* 운영자 액션은 `recommendation_reviews`

### 4. 성과 리포트

* `ad_placements`
* `placement_performance_daily`
* 또는 placement_id 기준 `segment_metric_snapshots` treatment/baseline 비교

### 5. 로그 탭

* `audit_logs`
* `recommendation_reviews`

---
