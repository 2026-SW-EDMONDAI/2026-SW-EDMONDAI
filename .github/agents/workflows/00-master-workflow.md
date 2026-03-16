# Master Workflow (M1~M5)

## 순서
1. M1 Foundation
2. M2 Ingestion & Segmentation
3. M3 Funnel Analytics
4. M4 Recommendation & Review
5. M5 Report & Stabilization

## 병렬 원칙
- API/DB 계약 고정 전 병렬 구현 금지
- 계약 고정 후 FE/BE, Pipeline/Recommendation 병렬 가능
- QA는 전 단계 지속 병렬 검증

## 게이트 원칙
- 각 단계 완료 기준 통과 후 다음 단계 진행
- handoff는 `handoff-schema.yaml` 준수
