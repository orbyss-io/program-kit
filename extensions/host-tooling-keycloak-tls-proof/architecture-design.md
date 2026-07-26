# Program Kit Keycloak TLS and generated-profile conformance correction

Status: ready for validation and human review
Canonical identity:
`pkid:design:program-kit:host-tooling-keycloak-tls-proof@1.0.0`

## Outcome

The disposable Aspire-backed Keycloak fixture must prove the actual generated
Program Kit security profiles over HTTPS. It may not convert the provider to
HTTP, disable HTTPS metadata, accept arbitrary loopback certificates, or use a
browser-wide HTTPS-error bypass and then claim equivalent conformance.

This correction is additive. It does not change the exact approved
host-tooling 1.3.0 design or plan bytes. Implementation requires both the
active 1.3.0 approval and a separate approval of this review set.

## Runtime TLS

Deterministic generation emits no certificate or private-key material.
Only after a human starts the disposable integration profile may the fixture:

1. create one ephemeral fixture CA and one Keycloak server certificate under a
   unique owned runtime root;
2. configure the pinned Keycloak container for HTTPS and disable provider HTTP;
3. mount the server certificate and private key read-only;
4. bind exact issuer, metadata, token endpoint, hostname, subject alternative
   names, algorithms, and lifetimes;
5. trust only that fixture CA inside isolated test clients and browser state;
   and
6. delete every owned key, certificate, browser, process, container, and
   runtime artifact during bounded teardown.

No machine or user trust store is read as fixture authority or mutated.
Nothing may run certificate repair, `netsh`, Winsock/IP/DNS/proxy/firewall/
route/adapter configuration, or Docker-network reconfiguration.

## What must actually run

The acceptance lane executes the generated projections for:

- confidential server-side OIDC authorization code with PKCE;
- public-browser OIDC authorization code with PKCE and no client secret;
- JWT resource-server validation;
- OAuth client credentials; and
- RFC 8693 token exchange.

Raw protocol vectors remain valuable for adversarial cases, but they are
additive. They cannot substitute for generated-profile execution.

The proof covers issuer and metadata validation, redirect matching, PKCE,
state, nonce, signature, audience, scopes, access-token versus ID-token
separation, lifetime, replay rejection, client authentication, subject-token
provenance, issued token type, browser storage, logout, key rollover, wrong
secret, wrong issuer/audience, substituted certificate, and HTTP fallback.

## Execution environments

The full lane must pass in at least one exact supported Linux container
environment with reviewed .NET, Aspire, container-runtime, image, and browser
selections. This does not make a Dev Container, Aspire CLI, external runtime
wrapper, or external repository a Program Kit runtime dependency.

A Windows Aspire DCP failure before Keycloak resource creation is classified
as an environment blocker. It neither proves nor disproves provider behavior,
cannot satisfy the full lane, and must not trigger trust-store, networking,
provider-transport, or validation-policy changes.

## Durable evidence

Durable evidence may contain exact public versions and digests, selected
algorithm/profile identifiers, phase names, bounded timings, and redacted
success/failure classifications.

It may not contain passwords, client secrets, tokens, cookies, claims, private
keys, certificate identifiers, secret-reference identities, absolute runtime
paths, browser state, raw provider logs, or raw DCP configuration.

## Deliberately absent

- HTTP equivalence for an HTTPS-only profile.
- Global certificate trust or host network repair.
- Direct-Docker, Testcontainers, or Compose replacement for Aspire.
- Production certificate lifecycle or Keycloak provisioning.
- Persistent provider or browser state.
- Consumer-domain identity or authorization meaning.
- Automatic fixture, browser, container, or environment execution.
