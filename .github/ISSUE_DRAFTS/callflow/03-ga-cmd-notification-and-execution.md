# Issue Title
GA: Handle cmd notification and execute workflow

## Summary
Implement Gateway Agent command-processing path:
- Receive notification for new `Cgatewayagent/cmd` contentInstance
- Fetch referenced command resource
- Validate command equals `execute`
- Delete processed command contentInstance

## Scope
- Add callback endpoint/handler for IN-CSE notifications.
- Ensure duplicate notification safety (idempotent processing).
- Reject unsupported commands with clear logs.

## Out of Scope
- Notification delivery guarantees implemented by IN-CSE.
- Any IN-CSE queue/event internals.

## Acceptance Criteria
- [ ] GA processes `execute` commands end-to-end.
- [ ] Processed command contentInstance is deleted.
- [ ] Duplicate notifications do not cause inconsistent state.

## Dependencies
- 01 GA bootstrap IN-CSE resources for gateway
- 02 Orchestrator bootstrap and trigger

## Labels
- gateway-agent
- notifications
- sprint
- backend
