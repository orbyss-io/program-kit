# Program Kit Keycloak TLS and generated-profile proof intent

Status: review input only  
Owner: `pkid:domain:program-kit:toolkit`  
Parent review set: `pkid:approval:program-kit:host-tooling-review-set@1.3.0`

## Human request

Prepare a narrowly scoped, separately reviewed correction for the optional
Keycloak/Aspire local-test fixture after implementation review established that:

1. the pinned `Aspire.Hosting.Keycloak` adapter exposes Keycloak development
   transport over HTTP by default;
2. the approved Program Kit OIDC, JWT, client-credentials, and token-exchange
   profiles require explicit HTTPS metadata and token endpoints;
3. a permissive loopback certificate callback or browser-wide HTTPS-error
   bypass cannot prove those profiles;
4. raw protocol calls are useful but do not prove that the actual generated
   confidential-client, public-browser, JWT-resource-server, client-credentials,
   and token-exchange projections work together;
5. the current Windows host has a separately observed Aspire DCP control-plane
   startup/listener failure before Keycloak resource creation; application HTTP
   does not correct that control-plane failure; and
6. a Linux container environment is an acceptable supported execution
   environment for the disposable integration proof, but no external
   repository's domain semantics, runtime wrapper, or scripts become Program
   Kit dependencies.

## Required correction

- Preserve the exact approved host-tooling 1.3.0 design and implementation-plan
  bytes. This review set is additive and cannot retroactively alter their
  approval.
- Keep the Keycloak fixture optional, disposable, local-test-only, and
  provider-specific.
- Configure Keycloak itself for HTTPS rather than changing the secure Program
  Kit profiles to HTTP.
- Create certificate and private-key material only after the separately
  authorized fixture execution begins, inside one exact fixture-owned runtime
  root.
- Mount runtime TLS material read-only into the Keycloak container, disable the
  provider HTTP listener for the proof, and remove all owned material during
  bounded teardown.
- Never install, trust, remove, or otherwise mutate certificates in a machine
  or user trust store.
- Validate the exact fixture certificate or fixture CA through an isolated
  test-client trust boundary. Do not accept arbitrary loopback certificates,
  disable TLS validation, or use browser-wide `IgnoreHTTPSErrors`.
- Exercise the actual generated Program Kit projections for confidential OIDC,
  public-browser OIDC with PKCE, JWT resource-server validation, OAuth
  client-credentials, and RFC 8693 token exchange. Raw protocol vectors remain
  additive adversarial evidence.
- Keep tokens, cookies, browser state, passwords, client secrets, private keys,
  certificate identifiers, absolute runtime paths, raw provider logs, and raw
  DCP configuration out of durable evidence.
- Distinguish provider readiness, DCP control-plane readiness, generated-host
  readiness, protocol behavior, and browser behavior.
- Permit the full integration gate to run in a supported Linux container
  environment with an isolated container runtime. A Windows DCP failure before
  resource creation is environment-blocker evidence, not permission to weaken
  TLS or bypass the Aspire-backed requirement.

## Rejected alternatives

- Do not change Keycloak to HTTP while claiming that the same secure generated
  profiles passed.
- Do not set `RequireHttpsMetadata` to false.
- Do not use `ServerCertificateCustomValidationCallback` to accept any
  loopback certificate.
- Do not use Playwright `IgnoreHTTPSErrors`.
- Do not retry certificate-store repair, machine-root import, Winsock, IP,
  proxy, DNS, firewall, route, adapter, or Docker-network reconfiguration.
- Do not replace the Aspire-backed fixture with direct Docker, Testcontainers,
  Docker Compose, or provider-specific orchestration.
- Do not make a Dev Container runtime or the Aspire CLI a Program Kit runtime
  dependency.

## Approval boundary

This intent authorizes design work only. Implementation remains blocked until
the human explicitly approves the exact canonical design and implementation
plan digests produced from this review set.
