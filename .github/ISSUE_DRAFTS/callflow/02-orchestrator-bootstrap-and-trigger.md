# Issue Title
Orchestrator: Bootstrap AE and write initial cmd/data content

## Summary
Implement Orchestrator bootstrap against IN-CSE:
- Create AE `Corchestrator`
- Create initial `Cgatewayagent/data/<cin>` with MN-CSE target metadata
- Create initial `Cgatewayagent/cmd/<cin>` with command `execute`

## Scope
- Add API/client logic for contentInstance creation order (`data` then `cmd`).
- Validate payload schema before write.
- Add basic retry/backoff for transient write failures.

## Out of Scope
- Subscription internals inside IN-CSE.
- oneM2M CSE implementation changes.

## Acceptance Criteria
- [ ] Orchestrator can create initial data/content command pair.
- [ ] Command write occurs only after valid data write.
- [ ] Logs include correlation IDs/resource paths for tracing.

## Dependencies
- 01 GA bootstrap IN-CSE resources for gateway

## Labels
- orchestrator
- oneM2M-client
- sprint
- backend
