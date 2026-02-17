# Issue Title
GA: Bootstrap IN-CSE resources for gateway

## Summary
Implement Gateway Agent startup provisioning against IN-CSE:
- Create AE `Cgatewayagent`
- Create subscription for `Cgatewayagent/cmd`
- Create containers `Cgatewayagent/data` and `Cgatewayagent/cmd`

## Scope
- Add idempotent create logic (safe on restart).
- Handle `201 Created` and already-exists conditions.
- Externalize IN-CSE endpoint/originator config.

## Out of Scope
- Any changes to IN-CSE server internals.
- oneM2M spec extensions beyond required resources.

## Acceptance Criteria
- [ ] GA startup provisions required resources when missing.
- [ ] Re-running GA does not duplicate or break resources.
- [ ] Failures are logged with actionable context.

## Dependencies
- None

## Labels
- gateway-agent
- oneM2M-client
- sprint
- backend
