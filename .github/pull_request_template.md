## Summary

- milestone: M1/M2/M3/M4/M5
- owner-agent:
- related-issue:

## Contracts

- API contract changes:
- DB schema changes:
- Breaking change: yes/no

## Verification

- [ ] `pytest ...`
- [ ] `playwright ...`
- [ ] build/lint/typecheck

## Handoff

```yaml
handoff:
  agent: <agent-name>
  phase: <M1|M2|M3|M4|M5>
  status: <done|blocked|needs-review>
  outputs:
    code_changes: []
    schema_changes: []
    api_changes: []
    tests: []
  contracts:
    producer: <guarantee>
    consumer: <assumption>
  risks: []
  next_actions: []
```
