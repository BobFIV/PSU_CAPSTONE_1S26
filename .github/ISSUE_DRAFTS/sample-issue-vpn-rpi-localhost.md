# Issue Title
Run WireGuard VPN on rPI and localhost

## Summary
Set up and validate WireGuard VPN connectivity between Raspberry Pi (rPI) services and localhost development environment so oneM2M components can communicate securely across both endpoints.

## Problem / Context
Current development and integration flows assume direct network access. We need a VPN path to:
- Enable secure remote access to rPI-hosted services.
- Support local testing from localhost against rPI resources.
- Keep routing and addressing consistent for Sprint integration tasks.

## Scope
- Configure WireGuard peers as required for rPI and localhost.
- Verify bidirectional reachability (localhost -> rPI and rPI -> localhost where required).
- Update service endpoints/config values used by Gateway Agent and callbacks.
- Document startup steps and troubleshooting notes.

## Out of Scope
- Production hardening beyond basic secure setup.
- Full zero-trust architecture redesign.

## Acceptance Criteria
- [ ] rPI is connected to WireGuard and shows expected tunnel interface (for example `wg0`).
- [ ] localhost is connected to WireGuard and can resolve/reach rPI WireGuard IP.
- [ ] Required ports for app flow are reachable through WireGuard tunnel.
- [ ] Gateway Agent can execute core call flow against target endpoints.
- [ ] Callback path works through WireGuard (if applicable).
- [ ] README/runbook includes exact setup and validation commands.

## Technical Notes
- Suggested deliverables:
  - WireGuard peer config files/steps for rPI and localhost.
  - Updated app config for endpoint URLs.
  - Quick connectivity checks (`wg show`, `ping`, `curl`, or app-level health checks).

## Test Plan
1. Start WireGuard on rPI (`wg-quick up wg0`); capture tunnel IP.
2. Start WireGuard on localhost (`wg-quick up wg0`); verify route table includes WireGuard subnet.
3. Validate connectivity to app endpoints over WireGuard tunnel.
4. Run Sprint call-flow smoke test from Gateway Agent.
5. Confirm logs for successful request/response and callback behavior.

## Risks
- Route conflicts between local subnet and VPN subnet.
- Firewall/NAT rules blocking required ports.
- DNS or hostname mismatch between local and VPN contexts.

## Labels
- enhancement
- networking
- devops
- sprint

## Assignee
TBD

## Estimate
3-5 story points
