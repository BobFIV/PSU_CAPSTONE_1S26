# Issue Title
GA: Register with MN-CSE after restart

## Summary
Implement post-restart registration from Gateway Agent to MN-CSE as a separate AE (e.g., `GatewayAgentMN`) according to MSC.

## Scope
- Create AE against MN-CSE endpoint after MN startup.
- Use distinct AE naming from IN-CSE registration.
- Add retry with bounded backoff while MN is warming up.

## Out of Scope
- MN-CSE registration internals.
- CSE authentication subsystem changes.

## Acceptance Criteria
- [ ] GA successfully creates/registers AE on MN-CSE.
- [ ] Registration uses distinct AE name as required.
- [ ] Failure path logs are actionable for ops.

## Dependencies
- 04 GA data consumption + MN restart

## Labels
- gateway-agent
- mn-cse-integration
- sprint
- backend
