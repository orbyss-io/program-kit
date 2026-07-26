# Program Kit Keycloak TLS and generated-profile proof implementation plan

Status: ready for human decision after validation
Plan identity:
`pkid:plan:program-kit:host-tooling-keycloak-tls-proof@1.0.0`

This plan is corrective and additive. It requires the active approval of:

- `pkid:design:program-kit:host-tooling@1.3.0`
  (`sha256:a9ad015470f3996ea09811d57007ec4ab90e3b2cbff91245e625bfdd82ad0d57`);
- `pkid:plan:program-kit:host-tooling@1.3.0`
  (`sha256:8144a67d5d919211f87a2d30a4d7a870f299c126e138986c6f079e133734f9a5`);
  and
- `pkid:design:program-kit:host-tooling-keycloak-tls-proof@1.0.0`
  (`sha256:094459fa8813d04f3ab0f97764770d80564657d27be04762c78e6a726d9d6a11`).

It does not authorize implementation or fixture execution before a new human
approval.

## 1. Requirements

| Requirement | Required outcome |
| --- | --- |
| `PKKC-R001` | Preserve the approved host-tooling 1.3.0 design and plan bytes and require both approval sets for corrective implementation. |
| `PKKC-R002` | Configure the pinned Keycloak fixture for exact HTTPS-only provider transport using runtime-only fixture-owned TLS material. |
| `PKKC-R003` | Establish exact process-isolated client and browser trust without machine/user trust mutation, arbitrary certificate acceptance, or broad HTTPS-error bypass. |
| `PKKC-R004` | Run the actual generated confidential OIDC, public-browser OIDC, JWT resource-server, client-credentials, and token-exchange projections. |
| `PKKC-R005` | Keep direct protocol vectors additive and cover positive, adversarial, replay, key-rollover, and substitution behavior. |
| `PKKC-R006` | Require one passing exact Linux integration lane while classifying a pre-resource Windows DCP failure separately and safely. |
| `PKKC-R007` | Keep runtime certificates, keys, secrets, tokens, cookies, browser state, provider state, paths, and raw logs ephemeral and prove bounded teardown. |
| `PKKC-R008` | Forbid certificate-store, Winsock, IP, DNS, proxy, firewall, route, adapter, Docker-network, or other operating-system network/trust mutation. |
| `PKKC-R009` | Close W100 only after exact version, package, image, TLS, generated-consumer, evidence, determinism, redaction, and environment claims all pass. |

## 2. Exact starting inputs

- The exact approved host-tooling 1.3.0 design and plan digests above.
- The checkpoint implementation at commit `e4a0320`, which is explicitly
  incomplete and carries no completion claim.
- The exact corrective design and plan bytes from this review set after human
  approval.
- Repository-owned pinned .NET, Aspire, Keycloak, Playwright, schema, secret
  resolution, and security-profile source truth.

No sibling repository, external wrapper, ambient certificate, host trust
state, or remembered runtime experiment is an implementation input.

## 3. Work units

### `PKKC-W010` — fixture-owned TLS specialization

**Requirements:** `PKKC-R001`–`PKKC-R003`, `PKKC-R007`, `PKKC-R008`.

**Depends on:** approved PKHT-W025, PKHT-W050, PKHT-W052, PKHT-W055,
PKHT-W070, and the exact corrective approval.

**Allowed edits:** the checkpoint W100 Keycloak fixture descriptors,
generator, schemas, exact provider/TLS selection evidence, generated AppHost
source, generated fixture documentation, diagnostics, and focused unit/offline
conformance tests. Central version files may change only for an exact reviewed
dependency proven necessary by this work unit.

**Required outcomes:**

1. Remove the checkpoint's false assumption that the default Keycloak Aspire
   endpoint is HTTPS and remove every permissive certificate callback,
   `IgnoreHTTPSErrors`, HTTP-equivalence claim, and troubleshooting-only
   environment override.
2. Define a closed versioned fixture TLS descriptor covering CA and server
   certificate profiles, algorithms, key sizes, validity bounds, EKU, SAN,
   hostname, Keycloak file locations, HTTPS port, provider HTTP-disabled state,
   isolated trust mode, runtime-root ownership, cleanup, and redacted evidence.
3. Generate deterministic AppHost/runtime-helper source that creates private
   material only after explicit execution begins, under the exact fixture root.
   Generation itself emits no certificate, key, password, random value, or
   machine-specific path.
4. Mount the exact server certificate and key read-only into the pinned
   Keycloak resource and configure only the reviewed Keycloak HTTPS surface.
5. Provide exact .NET custom-root trust and an exact browser trust mechanism
   scoped to the fixture authority or certificate public key. Absence of that
   exact mechanism fails the selected browser lane.
6. Make cancellation and every failure enter bounded teardown, including
   partial certificate creation and partial AppHost/container startup.

**Verification:**

- Repeated offline generation is byte-identical and contains no private
  material, certificate identifiers, random values, absolute paths, or secret
  reference identities.
- Schema, model, generated source, JSON, lock, and evidence selections agree.
- Generated AppHost restore/build succeeds without starting resources.
- Focused cryptographic tests prove CA constraints, serverAuth EKU, SAN and
  hostname, allowed algorithms/key sizes, validity bounds, non-export after
  handoff where supported, exact trust success, substituted/self-signed/
  expired/wrong-name/wrong-EKU rejection, provider HTTP-disabled
  configuration, read-only mounts, cancellation, and complete owned-root
  cleanup.
- Source and test scans reject `RequireHttpsMetadata = false`,
  arbitrary loopback acceptance, `IgnoreHTTPSErrors`, trust-store tools,
  network-configuration tools, direct-Docker orchestration, durable private
  material, and unsafe evidence.

**Stop conditions:** stop if exact Keycloak HTTPS requires production
provisioning semantics, durable private material, host trust mutation, network
configuration, an unpinned external tool, a permissive validation bypass, or a
new Program Kit runtime dependency not reviewed by this design.

### `PKKC-W020` — generated-profile integration proof

**Requirements:** `PKKC-R003`–`PKKC-R008`.

**Depends on:** `PKKC-W010`.

**Allowed edits:** W100 conformance-only generated consumer topology, test
hosts, browser harness, protocol vectors, cross-platform test plumbing,
isolated exact environment selection evidence, redacted result model,
documentation, and focused test-project/package references. No external
repository or wrapper files may be copied or referenced.

**Required outcomes:**

1. Compose actual generated Program Kit confidential OIDC, public-browser OIDC,
   JWT resource-server, client-credentials, and RFC 8693 token-exchange
   projections against the TLS-enabled Keycloak fixture.
2. Keep direct HTTP/protocol helpers only for adversarial vectors not already
   observable through generated consumers; label their evidence as additive.
3. Prove discovery, confidential and public authorization code with PKCE,
   redirect/origin/state/nonce validation, access-token versus ID-token
   separation, JWT signature/issuer/audience/lifetime validation, protected API
   allow/deny, service token acquisition, exact scope/resource/audience,
   subject-token provenance, requested/issued token type, token exchange,
   logout, replay rejection, wrong secret, wrong certificate, HTTP fallback,
   key rollover, browser storage non-retention, and token/cookie non-disclosure.
4. Run a Chromium baseline through exact isolated certificate trust. Keep
   Firefox and WebKit compatibility declarations truthful: they pass only where
   an exact isolated trust mechanism is implemented; otherwise they remain
   separately reported and cannot be claimed.
5. Make the standard integration test project cross-platform. Select and
   evidence one exact Linux container environment before execution; the
   environment supplies tooling only and owns no Program Kit semantics.
6. Recognize only a reviewed pre-resource Windows DCP blocker fingerprint as an
   environment blocker. Unknown failures fail normally. No blocker satisfies
   the Linux integration lane or triggers remediation commands.

**Verification:**

- Offline generated-consumer builds and runtime dependency scans prove no
  Program Kit generator/runtime dependency leakage.
- A separately human-started exact Linux integration lane starts the Aspire
  resource, completes every generated-profile and adversarial checkpoint,
  captures only redacted phase outcomes, and tears down all owned state.
- Negative tests prove failure when any generated role is replaced by direct
  protocol emulation, TLS is disabled, trust is broadened, a certificate is
  substituted, HTTP is enabled, Keycloak/Aspire/image/browser revisions drift,
  a secret/token/path enters evidence, or a process/container/root remains.
- A bounded Windows classification test uses synthetic sanitized failure input;
  it runs no network or certificate remediation.

**Stop conditions:** stop if a passing lane requires host networking/trust
changes, provider HTTP, certificate-validation bypass, automatic environment
execution, external repository semantics, direct-Docker replacement, captured
credentials, or omission of an actual generated profile.

### `PKKC-W030` — W100 corrective closure

**Requirements:** `PKKC-R001`, `PKKC-R006`–`PKKC-R009`.

**Depends on:** `PKKC-W020`.

**Allowed edits:** W100 locks, evidence, schema/module/version registration,
package closure, test-plan selection, generated fixture documentation,
independent review, bounded remediation, and the host-tooling review manifest's
implementation-status evidence. The approved 1.3.0 design, plan, and approval
records remain byte-identical.

**Required outcomes:**

1. Reconcile every checkpoint file against both approved designs and remove
   stale HTTP/HTTPS, certificate, generated-profile, package, version, or
   completion claims.
2. Freeze exact public package, image, source, TLS-profile, browser, and Linux
   environment selections and prove their package/image/source/license closure.
3. Bind deterministic offline results and the separately authorized full
   integration result without retaining sensitive or machine-specific data.
4. Run independent scope, security, secret, teardown, determinism,
   cross-platform, package, and evidence review.
5. Mark PKHT-W100 complete only if every corrective requirement and original
   W100 outcome passes. Otherwise retain an explicit incomplete state.
6. Resume original PKHT-W110 only after truthful W100 completion; do not add
   analyzer-follow-on implementation to this review set.

**Verification:** exact parent-design/plan hash check; corrective-design/plan
hash check; schema/module validation; locked restore; format; strict Release
build; focused and full unit/conformance suites; C# source gate; generated
consumer builds; exact package contents and dependency closure; deterministic
tree digests; secret/path/log redaction scan; container/process/runtime-root
teardown proof; independent review with no material finding; clean worktree;
and pushed commit identity matching the reviewed result.

**Stop conditions:** stop on any parent artifact byte change, unresolved
security finding, missing generated role, unpassed exact Linux lane, false
Windows completion claim, residual sensitive/runtime state, unpinned
dependency, package leakage, or material deviation from either approved
design.

## 4. Dependency order

`PKKC-W010` → `PKKC-W020` → `PKKC-W030` → original `PKHT-W110`.

No corrective work unit is parallel with another because TLS, generated
consumers, integration evidence, and closure are materially dependent.

## 5. Requirement trace

| Requirement | Work unit(s) |
| --- | --- |
| `PKKC-R001` | `PKKC-W010`, `PKKC-W030` |
| `PKKC-R002` | `PKKC-W010` |
| `PKKC-R003` | `PKKC-W010`, `PKKC-W020` |
| `PKKC-R004`–`PKKC-R005` | `PKKC-W020` |
| `PKKC-R006` | `PKKC-W020`, `PKKC-W030` |
| `PKKC-R007`–`PKKC-R008` | every corrective work unit |
| `PKKC-R009` | `PKKC-W030` |

## 6. Deliberately unimplemented

The correction does not add production PKI, certificate renewal/rotation,
Keycloak production provisioning, a reusable identity-provider test platform,
direct Docker/Testcontainers/Compose orchestration, automatic Dev Container or
Linux environment startup, Aspire CLI dependency, external-repository runtime
dependency, host certificate/network repair, HTTP security profiles, generic
browser trust management, consumer-domain identity/authorization, deployment,
release, or analyzer implementation.

## 7. Completion rule

This corrective plan is complete only after `PKKC-W030` passes every required
gate. A passing offline build, raw protocol exchange, Keycloak container start,
Windows blocker classification, or subset of generated roles is not
completion.
