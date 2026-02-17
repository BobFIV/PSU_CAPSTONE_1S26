# Issue Title
Orchestrator: Steady-state gateway config updates via data resource

## Summary
Implement Orchestrator steady-state update path by creating new contentInstances in gateway data resources when configuration changes (for example port updates), allowing IN-CSE notification fan-out to Gateway Agent.

## Scope
- Detect/update desired gateway config from orchestrator state.
- Write new data contentInstance to target resource path.
- Ensure update events are traceable and versioned.

## Out of Scope
- Notification dispatch internals in IN-CSE.
- Gateway Agent internal application of updates (handled in GA issues).

## Acceptance Criteria
- [ ] Config changes produce new data contentInstances.
- [ ] Resource path and payload format match GA expectations.
- [ ] Logs show update reason, target gateway, and contentInstance ID.

## Dependencies
- 02 Orchestrator bootstrap and trigger
- 04 GA data consumption + MN restart

## Labels
- orchestrator
- configuration
- sprint
- backend
