# Program Kit 0.8.1 compatibility report

0.8.1 is the corrective successor to the withdrawn 0.8.0 release. Governance lifecycle, managed OpenAPI,
SPA serving-security, toolchain, persistence-profile, ownership, and UTF-8 improvements remain available.

## Automatic upgrade

- Workflow/bundle updates preserve unrelated hooks and install the mandatory clarify/analyze lifecycle.
- Managed sync adds `runnable_host.py` and `runnable-host.schema.json`.
- The old managed application-bundle builder/schema are removed only when their current hashes equal the
  recorded installed hashes. Modified copies are preserved and reported as conflicts.
- No persistence provider or readiness client is added to the host.

## Review required

- `hostsettings.json` and `shells.json` remain scaffold-once consumer-owned. Existing `hostsettings.json`
  must configure the Nuplane directory feed path explicitly; the new shallow host does not inject one.
- Existing application Dockerfiles update automatically only if still hash-current. A customized Dockerfile
  must be changed to copy `artifacts/runnable-host/packages`, `hostsettings.json`, and `shells.json` directly.
- Any application that relied on host-provided authentication, OpenAPI, BFF endpoints, or health endpoints
  must select feature-owned replacements. 0.8.1 intentionally provides no compatibility shim inside the host.
- Deployment health checks require an application-owned endpoint/contract. Program Kit does not infer
  feature dependency readiness before CShells defines a contribution interface.

Previously generated repositories can otherwise retain their domain/features, `shells.json` activation,
managed build/OpenAPI capability, web SPA adapter, persistence selection, and governance evidence.
PriceCalculator was not modified.
