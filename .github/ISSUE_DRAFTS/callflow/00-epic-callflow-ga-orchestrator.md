# Issue Title
Epic: Implement Gateway Agent + Orchestrator callflow (CSE out of scope)

## Summary
Deliver the Sprint callflow between Orchestrator Application and Gateway Agent using oneM2M resources hosted by IN-CSE, while treating oneM2M CSE internals as an external dependency.

## Scope
- Implement Gateway Agent behaviors shown in MSC.
- Implement Orchestrator behaviors shown in MSC.
- Define request/response contracts, retries, and logging for integration.
- Deliver smoke tests for bootstrap and steady-state update flows.

## Out of Scope
- Implementing or modifying oneM2M CSE internals (IN-CSE/MN-CSE platform code).
- ACME feature development, persistence internals, or notification engine changes.

## Child Issues
- [ ] 01 GA bootstrap resources on IN-CSE
- [ ] 02 Orchestrator bootstrap + initial trigger write
- [ ] 03 GA notification endpoint + command execution
- [ ] 04 GA data consumption + config update + MN restart
- [ ] 05 GA registration with MN-CSE after restart
- [ ] 06 Orchestrator steady-state config updates
- [ ] 07 End-to-end smoke tests and observability

## Acceptance Criteria
- [ ] Child issues are complete and linked.
- [ ] End-to-end flow matches `media/msc.puml` behavior.
- [ ] README/runbook documents bootstrap and steady-state operation.

## Labels
- epic
- sprint
- integration
- gateway-agent
- orchestrator
