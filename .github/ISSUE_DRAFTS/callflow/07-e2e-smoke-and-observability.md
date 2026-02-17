# Issue Title
E2E: Validate callflow and add observability for GA + Orchestrator

## Summary
Add smoke tests and structured logs to validate bootstrap and steady-state behavior end-to-end across Gateway Agent and Orchestrator.

## Scope
- Define smoke sequence based on `media/msc.puml`.
- Add structured log fields (component, AE, resource path, operation, result).
- Document troubleshooting checks and expected outputs.

## Out of Scope
- oneM2M CSE performance tuning or internal instrumentation.
- Load/performance testing beyond smoke coverage.

## Acceptance Criteria
- [ ] Bootstrap flow passes from Orchestrator trigger to GA/MN registration.
- [ ] Steady-state update flow passes on data change.
- [ ] Logs are sufficient to trace a single request through both components.
- [ ] README/runbook includes operator steps for smoke validation.

## Dependencies
- 01 through 06

## Labels
- testing
- observability
- sprint
- integration
