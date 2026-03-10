# SegmentFlow API 명세서 v1

## 범위

이 명세서는 다음 핵심 흐름을 지원한다.

1. 교육영상 등록
2. 영상 분석 실행
3. 세그먼트 조회 및 수정
4. 세그먼트 학습 퍼널 조회
5. Agent 광고 위치 추천 생성
6. 추천 승인 / 수정 / 적용
7. 성과 리포트 조회
8. 학습 이벤트 수집

---

# 1. API 기본 규칙

## 1.1 Base URL

```text
https://api.segmentflow.com/api/v1
```

---

## 1.2 인증 방식

### 운영자 API

```http
Authorization: Bearer <JWT>
```

### 플레이어 이벤트 API

```http
X-Player-Token: <signed_token>
```

---

## 1.3 멀티테넌시 규칙

운영자 API는 조직 단위로 path를 구분한다.

```text
/api/v1/orgs/{orgId}/...
```

`orgId`는 JWT의 소속 조직과 일치해야 한다.

---

## 1.4 JSON 규칙

* 요청/응답은 기본적으로 `application/json`
* 파일 업로드는 `multipart/form-data`
* API 필드명은 **camelCase**
* DB 컬럼명은 **snake_case**

예:

* API: `segmentSetId`
* DB: `segment_set_id`

---

## 1.5 시간/숫자 규칙

* 시간: ISO 8601 UTC (`2026-03-10T12:30:00Z`)
* 영상 위치: `ms`
* rate 값: `0.0 ~ 1.0`
* percentage point 변화량은 별도 수치로 반환 가능

---

## 1.6 공통 응답 포맷

### 성공

```json
{
  "data": {},
  "meta": {
    "requestId": "req_01HXYZ...",
    "timestamp": "2026-03-10T12:30:00Z"
  }
}
```

### 에러

```json
{
  "error": {
    "code": "SEGMENT_SET_NOT_DRAFT",
    "message": "Only draft segment sets can be edited.",
    "details": {
      "segmentSetId": "9e9d..."
    }
  },
  "meta": {
    "requestId": "req_01HXYZ...",
    "timestamp": "2026-03-10T12:31:10Z"
  }
}
```

---

## 1.7 주요 HTTP Status

* `200 OK`: 정상 조회/수정
* `201 Created`: 리소스 생성
* `202 Accepted`: 비동기 작업 접수
* `204 No Content`: 삭제/비활성화 완료
* `400 Bad Request`: 요청 형식 오류
* `401 Unauthorized`: 인증 실패
* `403 Forbidden`: 권한 부족
* `404 Not Found`: 리소스 없음
* `409 Conflict`: 상태 충돌
* `422 Unprocessable Entity`: 도메인 검증 실패

---

## 1.8 페이지네이션

목록 API는 기본적으로 아래 형식을 사용한다.

### 요청

```http
GET /api/v1/orgs/{orgId}/videos?page=1&pageSize=20
```

### 응답

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 132,
    "requestId": "req_...",
    "timestamp": "2026-03-10T12:30:00Z"
  }
}
```

---

# 2. 권한 모델

| 역할       | 권한                       |
| -------- | ------------------------ |
| admin    | 전체 조회/수정/정책 변경/적용        |
| operator | 영상 등록, 세그먼트 수정, 추천 승인/적용 |
| analyst  | 조회 중심, 추천 생성 가능, 적용 불가   |

---

# 3. 주요 DTO 정의

## 3.1 Video

```json
{
  "id": "uuid",
  "organizationId": "uuid",
  "title": "기초 수학 교육영상 1",
  "description": "분수 개념 설명",
  "status": "analyzed",
  "durationMs": 1800000,
  "sourceType": "upload",
  "uploadedBy": "uuid",
  "analyzedAt": "2026-03-10T12:30:00Z",
  "createdAt": "2026-03-10T11:00:00Z",
  "updatedAt": "2026-03-10T12:30:00Z"
}
```

## 3.2 SegmentSet

```json
{
  "id": "uuid",
  "videoId": "uuid",
  "versionNo": 2,
  "status": "draft",
  "source": "hybrid",
  "createdBy": "uuid",
  "notes": "운영자 수정본",
  "createdAt": "2026-03-10T12:00:00Z",
  "updatedAt": "2026-03-10T12:20:00Z"
}
```

## 3.3 Segment

```json
{
  "id": "uuid",
  "segmentSetId": "uuid",
  "seqNo": 4,
  "startMs": 360000,
  "endMs": 520000,
  "title": "분수의 기본 원리",
  "topic": "fraction-basics",
  "keyConcepts": ["분수", "분자", "분모"],
  "summary": "분수의 구성 요소를 설명하는 구간",
  "sourceType": "edited"
}
```

## 3.4 SegmentMetric

```json
{
  "segmentId": "uuid",
  "metricDate": "2026-03-10",
  "cohortType": "all",
  "viewersStarted": 1200,
  "viewersCompleted": 910,
  "completionRate": 0.7583,
  "dropoutRate": 0.2417,
  "rewatchRate": 0.1880,
  "nextTransitionRate": 0.7012,
  "avgPauseCount": 1.42,
  "avgSeekBackCount": 0.67,
  "avgSpeedChangeCount": 0.19,
  "explicitResponseRate": 0.2240,
  "confidencePositiveRate": 0.61,
  "confidenceUnsureRate": 0.25,
  "confidenceReviewAgainRate": 0.14,
  "learningStabilityScore": 0.73
}
```

## 3.5 RecommendationCandidate

```json
{
  "id": "uuid",
  "recommendationRunId": "uuid",
  "videoId": "uuid",
  "segmentId": "uuid",
  "placementType": "after_segment",
  "placementTimeMs": 520000,
  "rankNo": 1,
  "confidenceScore": 0.86,
  "riskLevel": "low",
  "expectedCtrLift": 0.0520,
  "expectedCompletionImpact": -0.0110,
  "expectedTransitionImpact": -0.0090,
  "status": "proposed",
  "rationaleSummary": "세그먼트 종료 시점이 개념 전환점이며 직전 학습 신호가 안정적입니다."
}
```

---

# 4. 운영자 API

---

## 4.1 대시보드

### 4.1.1 대시보드 요약 조회

```http
GET /orgs/{orgId}/dashboard/summary
```

### 목적

대시보드 KPI 카드, 추천 대기, 경고 영상을 조회한다.

### Query

* `dateFrom` (optional)
* `dateTo` (optional)

### Response `200`

```json
{
  "data": {
    "kpis": {
      "totalVideos": 128,
      "analyzedVideos": 92,
      "pendingRecommendations": 14,
      "guardrailWarnings": 3
    },
    "recentAnalyzedVideos": [
      {
        "videoId": "uuid",
        "title": "교육영상 A",
        "analyzedAt": "2026-03-10T12:00:00Z"
      }
    ],
    "pendingItems": [
      {
        "videoId": "uuid",
        "title": "교육영상 B",
        "candidateCount": 2,
        "status": "pending_review"
      }
    ],
    "warnings": [
      {
        "videoId": "uuid",
        "title": "교육영상 D",
        "type": "transition_drop",
        "message": "다음 세그먼트 이동률 저하"
      }
    ]
  },
  "meta": {
    "requestId": "req_123",
    "timestamp": "2026-03-10T12:30:00Z"
  }
}
```

---

## 4.2 영상 관리

### 4.2.1 영상 목록 조회

```http
GET /orgs/{orgId}/videos
```

### Query

* `status` optional
* `recommendationStatus` optional
* `guardrailStatus` optional
* `page` optional
* `pageSize` optional
* `search` optional

### Response `200`

```json
{
  "data": [
    {
      "id": "uuid",
      "title": "교육영상 A",
      "status": "analyzed",
      "durationMs": 1800000,
      "latestSegmentCount": 11,
      "latestRecommendationStatus": "pending",
      "guardrailStatus": "normal",
      "analyzedAt": "2026-03-10T12:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 92,
    "requestId": "req_123",
    "timestamp": "2026-03-10T12:30:00Z"
  }
}
```

---

### 4.2.2 신규 영상 등록

```http
POST /orgs/{orgId}/videos
Content-Type: multipart/form-data
```

### 목적

영상 파일과 자막 파일을 업로드하고 분석 대상 영상을 생성한다.

### Form fields

* `title` required
* `description` optional
* `videoFile` required
* `subtitleFile` optional
* `sourceType` required (`upload`)
* `confidenceCheckEnabled` optional boolean
* `quizEnabled` optional boolean
* `conceptSelectEnabled` optional boolean
* `summaryEnabled` optional boolean

### Response `201`

```json
{
  "data": {
    "video": {
      "id": "uuid",
      "title": "기초 수학 교육영상 1",
      "status": "uploaded",
      "durationMs": 1800000,
      "sourceType": "upload",
      "createdAt": "2026-03-10T11:00:00Z"
    },
    "signalConfig": {
      "confidenceCheckEnabled": true,
      "quizEnabled": false,
      "conceptSelectEnabled": false,
      "summaryEnabled": false
    }
  },
  "meta": {
    "requestId": "req_124",
    "timestamp": "2026-03-10T11:00:00Z"
  }
}
```

---

### 4.2.3 영상 상세 조회

```http
GET /orgs/{orgId}/videos/{videoId}
```

### Response `200`

```json
{
  "data": {
    "video": {
      "id": "uuid",
      "organizationId": "uuid",
      "title": "기초 수학 교육영상 1",
      "description": "분수 개념 설명",
      "status": "analyzed",
      "durationMs": 1800000,
      "sourceType": "upload",
      "analyzedAt": "2026-03-10T12:30:00Z",
      "createdAt": "2026-03-10T11:00:00Z",
      "updatedAt": "2026-03-10T12:30:00Z"
    },
    "latestSegmentSet": {
      "id": "uuid",
      "versionNo": 1,
      "status": "draft"
    },
    "latestRecommendationRun": {
      "id": "uuid",
      "status": "succeeded"
    }
  },
  "meta": {
    "requestId": "req_125",
    "timestamp": "2026-03-10T12:31:00Z"
  }
}
```

---

### 4.2.4 영상 기본 정보 수정

```http
PATCH /orgs/{orgId}/videos/{videoId}
```

### Request

```json
{
  "title": "기초 수학 교육영상 1 - 수정",
  "description": "분수 개념 설명(개정판)"
}
```

### Response `200`

```json
{
  "data": {
    "id": "uuid",
    "title": "기초 수학 교육영상 1 - 수정",
    "description": "분수 개념 설명(개정판)",
    "updatedAt": "2026-03-10T12:40:00Z"
  },
  "meta": {
    "requestId": "req_126",
    "timestamp": "2026-03-10T12:40:00Z"
  }
}
```

---

### 4.2.5 영상 분석 실행

```http
POST /orgs/{orgId}/videos/{videoId}/analyze
```

### 목적

자막 처리, 세그먼트 생성, 학습 퍼널 초기 분석을 비동기로 실행한다.

### Request

```json
{
  "regenerateSegments": true,
  "captionSource": "default"
}
```

### Response `202`

```json
{
  "data": {
    "videoId": "uuid",
    "status": "processing",
    "message": "Analysis job accepted."
  },
  "meta": {
    "requestId": "req_127",
    "timestamp": "2026-03-10T12:45:00Z"
  }
}
```

---

## 4.3 명시적 신호 설정

### 4.3.1 영상별 신호 설정 조회

```http
GET /orgs/{orgId}/videos/{videoId}/signal-config
```

### Response `200`

```json
{
  "data": {
    "videoId": "uuid",
    "confidenceCheckEnabled": true,
    "quizEnabled": false,
    "conceptSelectEnabled": false,
    "summaryEnabled": false,
    "configJson": {}
  },
  "meta": {
    "requestId": "req_128",
    "timestamp": "2026-03-10T12:50:00Z"
  }
}
```

---

### 4.3.2 영상별 신호 설정 수정

```http
PATCH /orgs/{orgId}/videos/{videoId}/signal-config
```

### Request

```json
{
  "confidenceCheckEnabled": true,
  "quizEnabled": true,
  "conceptSelectEnabled": false,
  "summaryEnabled": false
}
```

### Response `200`

```json
{
  "data": {
    "videoId": "uuid",
    "confidenceCheckEnabled": true,
    "quizEnabled": true,
    "conceptSelectEnabled": false,
    "summaryEnabled": false,
    "updatedAt": "2026-03-10T12:55:00Z"
  },
  "meta": {
    "requestId": "req_129",
    "timestamp": "2026-03-10T12:55:00Z"
  }
}
```

---

## 4.4 세그먼트 버전 및 세그먼트 편집

### 수정 규칙

* `finalized` 상태의 `segmentSet`은 직접 수정할 수 없다.
* 수정하려면 먼저 clone해서 새로운 `draft` 버전을 생성해야 한다.

---

### 4.4.1 세그먼트 세트 목록 조회

```http
GET /orgs/{orgId}/videos/{videoId}/segment-sets
```

### Response `200`

```json
{
  "data": [
    {
      "id": "uuid",
      "versionNo": 1,
      "status": "finalized",
      "source": "auto",
      "createdAt": "2026-03-10T12:00:00Z"
    },
    {
      "id": "uuid2",
      "versionNo": 2,
      "status": "draft",
      "source": "hybrid",
      "createdAt": "2026-03-10T12:20:00Z"
    }
  ],
  "meta": {
    "requestId": "req_130",
    "timestamp": "2026-03-10T13:00:00Z"
  }
}
```

---

### 4.4.2 최신 세그먼트 세트 조회

```http
GET /orgs/{orgId}/videos/{videoId}/segment-sets/latest
```

### Response `200`

```json
{
  "data": {
    "id": "uuid2",
    "videoId": "uuid",
    "versionNo": 2,
    "status": "draft",
    "source": "hybrid"
  },
  "meta": {
    "requestId": "req_131",
    "timestamp": "2026-03-10T13:01:00Z"
  }
}
```

---

### 4.4.3 세그먼트 세트 복제

```http
POST /orgs/{orgId}/videos/{videoId}/segment-sets/{segmentSetId}/clone
```

### Request

```json
{
  "notes": "운영자 수정용 새 버전 생성"
}
```

### Response `201`

```json
{
  "data": {
    "id": "new-segment-set-uuid",
    "videoId": "video-uuid",
    "versionNo": 3,
    "status": "draft",
    "source": "hybrid",
    "notes": "운영자 수정용 새 버전 생성"
  },
  "meta": {
    "requestId": "req_132",
    "timestamp": "2026-03-10T13:05:00Z"
  }
}
```

---

### 4.4.4 세그먼트 세트 확정

```http
POST /orgs/{orgId}/videos/{videoId}/segment-sets/{segmentSetId}/finalize
```

### Response `200`

```json
{
  "data": {
    "segmentSetId": "uuid",
    "status": "finalized",
    "finalizedAt": "2026-03-10T13:10:00Z"
  },
  "meta": {
    "requestId": "req_133",
    "timestamp": "2026-03-10T13:10:00Z"
  }
}
```

---

### 4.4.5 세그먼트 목록 조회

```http
GET /orgs/{orgId}/segment-sets/{segmentSetId}/segments
```

### Response `200`

```json
{
  "data": [
    {
      "id": "seg1",
      "seqNo": 1,
      "startMs": 0,
      "endMs": 120000,
      "title": "개요",
      "topic": "intro",
      "keyConcepts": ["분수"],
      "summary": "도입부",
      "sourceType": "auto"
    }
  ],
  "meta": {
    "requestId": "req_134",
    "timestamp": "2026-03-10T13:12:00Z"
  }
}
```

---

### 4.4.6 세그먼트 수정

```http
PATCH /orgs/{orgId}/segment-sets/{segmentSetId}/segments/{segmentId}
```

### Request

```json
{
  "title": "분수의 기본 개념",
  "topic": "fraction-basics",
  "keyConcepts": ["분수", "분자", "분모"],
  "summary": "분수의 핵심 요소를 설명"
}
```

### Response `200`

```json
{
  "data": {
    "id": "segment-uuid",
    "segmentSetId": "segment-set-uuid",
    "seqNo": 4,
    "startMs": 360000,
    "endMs": 520000,
    "title": "분수의 기본 개념",
    "topic": "fraction-basics",
    "keyConcepts": ["분수", "분자", "분모"],
    "summary": "분수의 핵심 요소를 설명",
    "sourceType": "edited",
    "updatedAt": "2026-03-10T13:15:00Z"
  },
  "meta": {
    "requestId": "req_135",
    "timestamp": "2026-03-10T13:15:00Z"
  }
}
```

---

### 4.4.7 세그먼트 분할

```http
POST /orgs/{orgId}/segment-sets/{segmentSetId}/segments/{segmentId}/split
```

### Request

```json
{
  "splitAtMs": 440000
}
```

### Response `201`

```json
{
  "data": {
    "originalSegmentId": "segment-uuid",
    "newSegments": [
      {
        "id": "seg-a",
        "seqNo": 4,
        "startMs": 360000,
        "endMs": 440000
      },
      {
        "id": "seg-b",
        "seqNo": 5,
        "startMs": 440000,
        "endMs": 520000
      }
    ]
  },
  "meta": {
    "requestId": "req_136",
    "timestamp": "2026-03-10T13:20:00Z"
  }
}
```

---

### 4.4.8 세그먼트 병합

```http
POST /orgs/{orgId}/segment-sets/{segmentSetId}/segments/merge
```

### Request

```json
{
  "segmentIds": ["seg-a", "seg-b"]
}
```

### Response `201`

```json
{
  "data": {
    "mergedSegment": {
      "id": "seg-merged",
      "seqNo": 4,
      "startMs": 360000,
      "endMs": 520000,
      "title": "병합된 세그먼트"
    }
  },
  "meta": {
    "requestId": "req_137",
    "timestamp": "2026-03-10T13:22:00Z"
  }
}
```

---

## 4.5 자막 조회

### 4.5.1 자막 구간 조회

```http
GET /orgs/{orgId}/videos/{videoId}/captions/cues
```

### Query

* `startMs` optional
* `endMs` optional
* `languageCode` optional

### Response `200`

```json
{
  "data": [
    {
      "seqNo": 1,
      "startMs": 0,
      "endMs": 4000,
      "text": "오늘은 분수의 개념을 배워보겠습니다."
    }
  ],
  "meta": {
    "requestId": "req_138",
    "timestamp": "2026-03-10T13:25:00Z"
  }
}
```

---

## 4.6 학습 퍼널 / 지표 조회

### 4.6.1 영상 학습 퍼널 조회

```http
GET /orgs/{orgId}/videos/{videoId}/funnel
```

### Query

* `segmentSetId` required
* `metricDate` optional
* `cohortType` optional (`all`, `baseline`, `treatment`)
* `placementId` optional

### Response `200`

```json
{
  "data": {
    "videoSummary": {
      "videoId": "uuid",
      "segmentSetId": "uuid",
      "metricDate": "2026-03-10",
      "completionRate": 0.72,
      "nextTransitionRate": 0.65,
      "explicitResponseRate": 0.24
    },
    "segments": [
      {
        "segment": {
          "id": "seg-1",
          "seqNo": 1,
          "title": "개요",
          "startMs": 0,
          "endMs": 120000
        },
        "metrics": {
          "viewersStarted": 1200,
          "viewersCompleted": 1100,
          "completionRate": 0.9167,
          "dropoutRate": 0.0833,
          "rewatchRate": 0.08,
          "nextTransitionRate": 0.89,
          "avgPauseCount": 1.2,
          "avgSeekBackCount": 0.4,
          "explicitResponseRate": 0.28,
          "confidencePositiveRate": 0.66,
          "confidenceUnsureRate": 0.22,
          "confidenceReviewAgainRate": 0.12,
          "learningStabilityScore": 0.81
        },
        "riskFlags": []
      },
      {
        "segment": {
          "id": "seg-4",
          "seqNo": 4,
          "title": "분수의 기본 원리",
          "startMs": 360000,
          "endMs": 520000
        },
        "metrics": {
          "viewersStarted": 880,
          "viewersCompleted": 610,
          "completionRate": 0.6932,
          "dropoutRate": 0.3068,
          "rewatchRate": 0.29,
          "nextTransitionRate": 0.54,
          "avgPauseCount": 2.8,
          "avgSeekBackCount": 1.9,
          "explicitResponseRate": 0.15,
          "confidencePositiveRate": 0.43,
          "confidenceUnsureRate": 0.34,
          "confidenceReviewAgainRate": 0.23,
          "learningStabilityScore": 0.42
        },
        "riskFlags": ["dropout_spike", "rewatch_spike", "low_explicit_signal"]
      }
    ]
  },
  "meta": {
    "requestId": "req_139",
    "timestamp": "2026-03-10T13:30:00Z"
  }
}
```

---

### 4.6.2 특정 세그먼트 시계열 지표 조회

```http
GET /orgs/{orgId}/segments/{segmentId}/metrics/timeseries
```

### Query

* `dateFrom` required
* `dateTo` required
* `cohortType` optional
* `placementId` optional

### Response `200`

```json
{
  "data": {
    "segmentId": "seg-4",
    "series": [
      {
        "metricDate": "2026-03-08",
        "completionRate": 0.71,
        "nextTransitionRate": 0.58,
        "explicitResponseRate": 0.19
      },
      {
        "metricDate": "2026-03-09",
        "completionRate": 0.69,
        "nextTransitionRate": 0.56,
        "explicitResponseRate": 0.17
      }
    ]
  },
  "meta": {
    "requestId": "req_140",
    "timestamp": "2026-03-10T13:31:00Z"
  }
}
```

---

## 4.7 추천 생성 / 조회 / 검토

### 4.7.1 추천 실행 생성

```http
POST /orgs/{orgId}/videos/{videoId}/recommendation-runs
```

### 목적

세그먼트 퍼널과 가드레일 정책을 기반으로 Agent 추천을 생성한다.

### Request

```json
{
  "segmentSetId": "segment-set-uuid",
  "guardrailPolicyId": "policy-uuid",
  "inputSnapshotDate": "2026-03-10"
}
```

### Response `202`

```json
{
  "data": {
    "recommendationRunId": "run-uuid",
    "status": "queued"
  },
  "meta": {
    "requestId": "req_141",
    "timestamp": "2026-03-10T13:35:00Z"
  }
}
```

---

### 4.7.2 추천 실행 목록 조회

```http
GET /orgs/{orgId}/videos/{videoId}/recommendation-runs
```

### Query

* `status` optional
* `page` optional
* `pageSize` optional

### Response `200`

```json
{
  "data": [
    {
      "id": "run-uuid",
      "status": "succeeded",
      "segmentSetId": "segment-set-uuid",
      "guardrailPolicyId": "policy-uuid",
      "modelVersion": "reco-v1.0.0",
      "inputSnapshotDate": "2026-03-10",
      "createdAt": "2026-03-10T13:35:00Z",
      "completedAt": "2026-03-10T13:36:10Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 3,
    "requestId": "req_142",
    "timestamp": "2026-03-10T13:36:30Z"
  }
}
```

---

### 4.7.3 추천 실행 상세 조회

```http
GET /orgs/{orgId}/recommendation-runs/{runId}
```

### Response `200`

```json
{
  "data": {
    "id": "run-uuid",
    "videoId": "video-uuid",
    "segmentSetId": "segment-set-uuid",
    "guardrailPolicyId": "policy-uuid",
    "status": "succeeded",
    "modelVersion": "reco-v1.0.0",
    "inputSnapshotDate": "2026-03-10",
    "inputSummary": {
      "segmentCount": 11,
      "explicitSignalEnabled": true
    },
    "createdAt": "2026-03-10T13:35:00Z",
    "completedAt": "2026-03-10T13:36:10Z"
  },
  "meta": {
    "requestId": "req_143",
    "timestamp": "2026-03-10T13:36:40Z"
  }
}
```

---

### 4.7.4 추천 후보 조회

```http
GET /orgs/{orgId}/recommendation-runs/{runId}/candidates
```

### Query

* `includeEvidence` optional boolean

### Response `200`

```json
{
  "data": [
    {
      "id": "cand-1",
      "recommendationRunId": "run-uuid",
      "videoId": "video-uuid",
      "segmentId": "seg-3",
      "placementType": "after_segment",
      "placementTimeMs": 520000,
      "rankNo": 1,
      "confidenceScore": 0.86,
      "riskLevel": "low",
      "expectedCtrLift": 0.052,
      "expectedCompletionImpact": -0.011,
      "expectedTransitionImpact": -0.009,
      "status": "proposed",
      "rationaleSummary": "개념 전환점이며 직전 신호가 안정적입니다.",
      "evidence": [
        {
          "signalMode": "implicit",
          "signalName": "completionRate",
          "signalValue": 0.84,
          "direction": "positive",
          "message": "직전 세그먼트 완료율이 높습니다."
        },
        {
          "signalMode": "explicit",
          "signalName": "confidencePositiveRate",
          "signalValue": 0.63,
          "direction": "positive",
          "message": "이해도 체크 긍정 반응 비율이 안정적입니다."
        },
        {
          "signalMode": "implicit",
          "signalName": "dropoutRate",
          "signalValue": 0.31,
          "direction": "exclusion",
          "message": "다음 세그먼트는 이탈 증가로 제외되었습니다."
        }
      ]
    }
  ],
  "meta": {
    "requestId": "req_144",
    "timestamp": "2026-03-10T13:37:00Z"
  }
}
```

---

### 4.7.5 추천 검토 액션 생성

```http
POST /orgs/{orgId}/recommendation-candidates/{candidateId}/reviews
```

### 목적

추천 후보에 대해 승인/반려/수정/메모를 남긴다.

### Request

```json
{
  "action": "modify",
  "modifiedPlacementTimeMs": 525000,
  "comment": "세그먼트 종료 후 5초 뒤에 노출하도록 조정"
}
```

### Response `201`

```json
{
  "data": {
    "id": "review-uuid",
    "candidateId": "cand-1",
    "reviewerId": "user-uuid",
    "action": "modify",
    "originalPlacementTimeMs": 520000,
    "modifiedPlacementTimeMs": 525000,
    "comment": "세그먼트 종료 후 5초 뒤에 노출하도록 조정",
    "createdAt": "2026-03-10T13:40:00Z"
  },
  "meta": {
    "requestId": "req_145",
    "timestamp": "2026-03-10T13:40:00Z"
  }
}
```

---

### 4.7.6 추천 적용

```http
POST /orgs/{orgId}/recommendation-candidates/{candidateId}/apply
```

### 목적

후보를 실제 광고 위치로 반영한다.
마지막 수정 리뷰가 있으면 그 위치를 우선 적용한다.

### Request

```json
{
  "placementTimeMs": 525000,
  "notes": "운영자 승인 후 실제 적용"
}
```

### Response `201`

```json
{
  "data": {
    "placementId": "placement-uuid",
    "videoId": "video-uuid",
    "candidateId": "cand-1",
    "segmentId": "seg-3",
    "placementTimeMs": 525000,
    "status": "applied",
    "appliedAt": "2026-03-10T13:45:00Z"
  },
  "meta": {
    "requestId": "req_146",
    "timestamp": "2026-03-10T13:45:00Z"
  }
}
```

---

## 4.8 추천 관리

### 4.8.1 추천 대기/상태 목록 조회

```http
GET /orgs/{orgId}/recommendations
```

### Query

* `status` optional (`proposed`, `approved`, `rejected`, `modified`, `applied`)
* `riskLevel` optional
* `page` optional
* `pageSize` optional

### Response `200`

```json
{
  "data": [
    {
      "candidateId": "cand-1",
      "videoId": "video-uuid",
      "videoTitle": "교육영상 B",
      "rankNo": 1,
      "confidenceScore": 0.86,
      "riskLevel": "low",
      "status": "proposed",
      "createdAt": "2026-03-10T13:36:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 14,
    "requestId": "req_147",
    "timestamp": "2026-03-10T13:46:00Z"
  }
}
```

---

## 4.9 광고 위치 / 성과 리포트

### 4.9.1 영상별 적용된 광고 위치 목록

```http
GET /orgs/{orgId}/videos/{videoId}/placements
```

### Response `200`

```json
{
  "data": [
    {
      "placementId": "placement-uuid",
      "candidateId": "cand-1",
      "segmentId": "seg-3",
      "placementTimeMs": 525000,
      "status": "applied",
      "appliedAt": "2026-03-10T13:45:00Z"
    }
  ],
  "meta": {
    "requestId": "req_148",
    "timestamp": "2026-03-10T13:50:00Z"
  }
}
```

---

### 4.9.2 광고 위치 성과 조회

```http
GET /orgs/{orgId}/placements/{placementId}/performance
```

### Query

* `dateFrom` required
* `dateTo` required

### Response `200`

```json
{
  "data": {
    "placementId": "placement-uuid",
    "daily": [
      {
        "metricDate": "2026-03-10",
        "impressions": 5100,
        "clicks": 190,
        "ctr": 0.0373,
        "revenue": 150.25,
        "exposedViewers": 4800,
        "exposedCompletionRate": 0.72,
        "exposedTransitionRate": 0.65,
        "exposedExplicitResponseRate": 0.23
      }
    ]
  },
  "meta": {
    "requestId": "req_149",
    "timestamp": "2026-03-10T13:55:00Z"
  }
}
```

---

### 4.9.3 영상 성과 리포트 조회

```http
GET /orgs/{orgId}/videos/{videoId}/reports/performance
```

### Query

* `dateFrom` required
* `dateTo` required
* `compareMode` optional (`before_after`, `baseline_vs_treatment`)
* `placementId` optional

### Response `200`

```json
{
  "data": {
    "videoId": "video-uuid",
    "compareMode": "before_after",
    "adPerformance": {
      "ctrBefore": 0.031,
      "ctrAfter": 0.038,
      "impressionsBefore": 10200,
      "impressionsAfter": 10050
    },
    "learningGuardrails": {
      "completionRateBefore": 0.74,
      "completionRateAfter": 0.72,
      "transitionRateBefore": 0.67,
      "transitionRateAfter": 0.65,
      "explicitPositiveBefore": 0.62,
      "explicitPositiveAfter": 0.61,
      "guardrailStatus": "normal"
    },
    "candidateComparisons": [
      {
        "candidateId": "cand-1",
        "ctrDelta": 0.007,
        "completionDelta": -0.020,
        "transitionDelta": -0.018,
        "explicitSignalDelta": -0.010,
        "status": "acceptable"
      }
    ]
  },
  "meta": {
    "requestId": "req_150",
    "timestamp": "2026-03-10T14:00:00Z"
  }
}
```

---

## 4.10 감사 로그

### 4.10.1 영상별 감사 로그 조회

```http
GET /orgs/{orgId}/videos/{videoId}/audit-logs
```

### Query

* `entityType` optional
* `page` optional
* `pageSize` optional

### Response `200`

```json
{
  "data": [
    {
      "id": "log-uuid",
      "entityType": "recommendation",
      "entityId": "cand-1",
      "action": "approved",
      "message": "추천안 #1 승인",
      "createdAt": "2026-03-10T13:40:00Z",
      "user": {
        "id": "user-uuid",
        "name": "김지훈"
      }
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 38,
    "requestId": "req_151",
    "timestamp": "2026-03-10T14:05:00Z"
  }
}
```

---

## 4.11 가드레일 정책

### 4.11.1 활성 가드레일 정책 조회

```http
GET /orgs/{orgId}/guardrail-policies/active
```

### Response `200`

```json
{
  "data": {
    "id": "policy-uuid",
    "name": "Default Policy",
    "completionDropLimitPp": 3.0,
    "transitionDropLimitPp": 3.0,
    "explicitSignalDropLimitPp": 5.0,
    "minConfidenceScore": 0.60,
    "isActive": true
  },
  "meta": {
    "requestId": "req_152",
    "timestamp": "2026-03-10T14:10:00Z"
  }
}
```

---

### 4.11.2 가드레일 정책 수정

```http
PATCH /orgs/{orgId}/guardrail-policies/{policyId}
```

### Request

```json
{
  "completionDropLimitPp": 3.0,
  "transitionDropLimitPp": 3.0,
  "explicitSignalDropLimitPp": 4.0,
  "minConfidenceScore": 0.65,
  "isActive": true
}
```

### Response `200`

```json
{
  "data": {
    "id": "policy-uuid",
    "completionDropLimitPp": 3.0,
    "transitionDropLimitPp": 3.0,
    "explicitSignalDropLimitPp": 4.0,
    "minConfidenceScore": 0.65,
    "isActive": true,
    "updatedAt": "2026-03-10T14:12:00Z"
  },
  "meta": {
    "requestId": "req_153",
    "timestamp": "2026-03-10T14:12:00Z"
  }
}
```

---

# 5. 플레이어 이벤트 API

이 API는 학습자의 시청/반응 데이터를 수집한다.

---

## 5.1 이벤트 배치 수집

```http
POST /player/events/batch
```

### 인증

```http
X-Player-Token: <signed_token>
```

### 목적

암묵적 신호, 명시적 신호, 광고 이벤트를 배치로 적재한다.

### Request

```json
{
  "organizationId": "org-uuid",
  "videoId": "video-uuid",
  "segmentSetId": "segment-set-uuid",
  "learnerSessionId": "session-uuid",
  "anonymousUserKey": "anon_abc123",
  "events": [
    {
      "clientEventId": "evt-1",
      "signalMode": "implicit",
      "eventType": "segment_start",
      "segmentId": "seg-1",
      "positionMs": 0,
      "occurredAt": "2026-03-10T12:00:10Z"
    },
    {
      "clientEventId": "evt-2",
      "signalMode": "implicit",
      "eventType": "pause",
      "segmentId": "seg-1",
      "positionMs": 45000,
      "payload": {
        "durationMs": 5000
      },
      "occurredAt": "2026-03-10T12:01:00Z"
    },
    {
      "clientEventId": "evt-3",
      "signalMode": "explicit",
      "eventType": "confidence_check_submit",
      "segmentId": "seg-1",
      "positionMs": 118000,
      "eventValue": "understood",
      "payload": {
        "option": "understood"
      },
      "occurredAt": "2026-03-10T12:02:00Z"
    },
    {
      "clientEventId": "evt-4",
      "signalMode": "ad",
      "eventType": "ad_impression",
      "segmentId": "seg-3",
      "positionMs": 525000,
      "payload": {
        "placementId": "placement-uuid"
      },
      "occurredAt": "2026-03-10T12:08:45Z"
    }
  ]
}
```

### Response `202`

```json
{
  "data": {
    "accepted": 4,
    "rejected": 0
  },
  "meta": {
    "requestId": "req_154",
    "timestamp": "2026-03-10T14:20:00Z"
  }
}
```

---

## 5.2 이벤트 수집 규칙

### 필수 필드

* `organizationId`
* `videoId`
* `segmentSetId`
* `learnerSessionId`
* `events[]`

### 이벤트별 추가 필드

* `segment_start`, `segment_complete`, `pause`, `seek_back`, `rewatch`, `next_segment_start`, `confidence_check_submit` → `segmentId` 권장
* `ad_impression`, `ad_click` → `payload.placementId` 권장

### `eventValue` 허용 예시

* `confidence_check_submit`

  * `understood`
  * `unsure`
  * `review_again`

---

## 5.3 중복 방지

`clientEventId`는 세션 내 유일해야 한다.
중복 수신 시 서버는 멱등 처리한다.

---

# 6. 주요 도메인 에러 코드

| code                         | 의미                  |
| ---------------------------- | ------------------- |
| VIDEO_NOT_FOUND              | 영상이 없음              |
| VIDEO_NOT_ANALYZED           | 분석 완료 전 영상          |
| SEGMENT_SET_NOT_FOUND        | 세그먼트 세트가 없음         |
| SEGMENT_SET_NOT_DRAFT        | draft가 아니라 수정 불가    |
| INVALID_SPLIT_POSITION       | 분할 위치가 세그먼트 범위를 벗어남 |
| SEGMENT_MERGE_NOT_CONTIGUOUS | 병합 대상 세그먼트가 연속되지 않음 |
| RECOMMENDATION_RUN_NOT_FOUND | 추천 실행 없음            |
| RECOMMENDATION_NOT_READY     | 추천 생성이 아직 완료되지 않음   |
| CANDIDATE_NOT_FOUND          | 추천 후보 없음            |
| REVIEW_ACTION_INVALID        | 잘못된 리뷰 액션           |
| GUARDRAIL_POLICY_NOT_FOUND   | 가드레일 정책 없음          |
| PLACEMENT_NOT_FOUND          | 광고 위치 없음            |
| EVENT_BATCH_INVALID          | 이벤트 배치 형식 오류        |
| PLAYER_TOKEN_INVALID         | 플레이어 토큰 유효하지 않음     |

---

# 7. 구현 우선순위 제안

## Phase 1: MVP 필수 API

가장 먼저 구현할 엔드포인트입니다.

1. `POST /orgs/{orgId}/videos`
2. `GET /orgs/{orgId}/videos`
3. `GET /orgs/{orgId}/videos/{videoId}`
4. `POST /orgs/{orgId}/videos/{videoId}/analyze`
5. `GET /orgs/{orgId}/videos/{videoId}/segment-sets/latest`
6. `GET /orgs/{orgId}/segment-sets/{segmentSetId}/segments`
7. `PATCH /orgs/{orgId}/segment-sets/{segmentSetId}/segments/{segmentId}`
8. `GET /orgs/{orgId}/videos/{videoId}/funnel`
9. `POST /orgs/{orgId}/videos/{videoId}/recommendation-runs`
10. `GET /orgs/{orgId}/recommendation-runs/{runId}/candidates`
11. `POST /orgs/{orgId}/recommendation-candidates/{candidateId}/reviews`
12. `POST /orgs/{orgId}/recommendation-candidates/{candidateId}/apply`
13. `POST /player/events/batch`

## Phase 2: 파일럿 운영

1. `GET /orgs/{orgId}/videos/{videoId}/reports/performance`
2. `GET /orgs/{orgId}/videos/{videoId}/audit-logs`
3. `GET /orgs/{orgId}/recommendations`
4. `PATCH /orgs/{orgId}/videos/{videoId}/signal-config`
5. `PATCH /orgs/{orgId}/guardrail-policies/{policyId}`

## Phase 3: 운영 고도화

1. 세그먼트 clone/finalize
2. split/merge
3. 시계열 지표 API
4. 캡션 cue API

---

# 8. 이 명세 기준으로 바로 연결되는 백엔드 모듈

이 API 명세를 그대로 구현 기준으로 나누면 서버 모듈은 아래처럼 분리하면 됩니다.

* `video-service`
* `segment-service`
* `analytics-service`
* `recommendation-service`
* `placement-service`
* `event-ingestion-service`
* `policy-service`
* `audit-service`

---