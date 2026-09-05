# Program Kit 0.9.0 evidence

The release validation covers the complete web-profile lifecycle and package boundary:

- fresh `none`, `bff-cookie`, and `spa-pkce` repositories;
- every directed transition between those profiles followed by an idempotence check;
- exact retirement of authenticated stale 0.8.11 SPA residue and preservation of modified residue;
- conflict detection before mutation, journaled atomic writes, injected failure rollback, and retry;
- separate BFF-cookie and SPA-PKCE CShell feature packages activated by the managed shell overlay;
- BFF anonymous-user endpoint behavior, SPA CORS preflight, security/correlation headers, and the
  default RFC 9457-compatible 401 response;
- clean `ProgramKit.Host` source and dependency boundaries, with no authentication, header,
  endpoint, OpenAPI, or exception-response policy in the host.

Runnable-host staging selects the active built-in feature packages, resolves their nearest
net10-compatible NuGet dependency groups, and records the managed profile shell overlay plus its
SHA-256 digest in the release descriptor.
