# Program Kit 0.8.9 compatibility report

0.8.9 is a security-corrective release for `spa-pkce-v1`. It preserves the profile identifier
because exact redirects, a public client, bounded sessions, and secret-safe evidence were already
the v1 contract; the implementation is being brought into conformance.

The update is operationally breaking for a SPA that relied on arbitrary paths below a wildcard
Keycloak registration. The new default registrations are:

- `http://localhost:5173/auth/callback`;
- `http://localhost:5173/auth/renew-callback`; and
- `http://localhost:5173/signed-out`.

Existing unchanged managed realm, compose, browser-contract, Playwright, launch, and test files are
updated automatically. A modified managed file remains a reported conflict. SPA `hostsettings.json`
becomes a managed derivative of `.program-kit/spa-pkce.json`; an existing modified copy must be
translated into that typed input before the conflict is resolved. Do not copy values into the
managed realm or Compose files.

Authentication traces, screenshots, and videos are disabled. CI jobs that expected a Playwright
failure trace must use non-authentication tests with a separately reviewed redaction and retention
policy; authentication journeys do not opt back into capture.

Local SPA process composition remains consumer-owned. Pass a repository-contained Compose overlay
to `eng/program-kit/Dev.ps1 -ComposeOverlay <path>`, or start the independently hosted SPA through its
own reviewed process. The managed application Compose file owns only the Program Kit API host.

Canonical `WEB-Cxx` meanings now come exclusively from the managed evidence registry. Existing
quality-system rows that used those IDs for sequential test cases must be renamed, for example to
`WEB-Qxx`, and mapped explicitly to the applicable canonical controls. This documentation-only
migration does not change the security controls themselves.

The OpenAPI registry remains empty until the first externally consumed contract. Use
`eng/program-kit/openapi_init.py` for that transition; no new oasdiff ADR is required. Existing
contracts must use managed oasdiff 1.29.1. A deliberate comparator override remains an architecture
decision and is not silently accepted.
