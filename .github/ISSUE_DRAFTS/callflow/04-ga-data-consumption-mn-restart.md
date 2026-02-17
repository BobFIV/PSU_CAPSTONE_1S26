# Issue Title
GA: Consume data content, update config, restart MN-CSE

## Summary
After command execution, Gateway Agent fetches `Cgatewayagent/data/<cin>`, applies values to local config, and restarts MN-CSE runtime in Docker.

## Scope
- Parse expected data payload fields (MN name/id and relevant endpoint values).
- Update config file atomically.
- Restart MN-CSE container/process and verify healthy startup.

## Out of Scope
- Modifying MN-CSE runtime internals.
- Changes to ACME image/source.

## Acceptance Criteria
- [ ] GA reads latest data contentInstance successfully.
- [ ] Config update is persisted and auditable.
- [ ] MN-CSE restart succeeds and health check passes.

## Dependencies
- 03 GA cmd notification and execution

## Labels
- gateway-agent
- docker
- configuration
- sprint
