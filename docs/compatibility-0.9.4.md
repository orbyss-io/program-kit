# Program Kit 0.9.4 compatibility report

0.9.4 preserves the independently packaged CShell web-feature model introduced in 0.9.0 and makes
its composition authoritative throughout the toolchain. Existing consumer `shells.json` settings
remain consumer-owned and take precedence over the selected profile baseline. Explicit `false`
continues to disable a profile default, including `ProgramKit.Web.ProblemDetails`, so consumers can
provide their own global exception handler and response format.

OpenAPI generation is intentionally stricter. It requires the selected profile's feature packages,
a coherent effective shell graph, a validated local toolchain, and fresh same-run runtime-closure
evidence. Repositories that previously exported against an incomplete or stale stage must rerun the
managed stage before export. The official `oasdiff` executable is required, but its current and
legacy version-reporting forms are both recognized.

Managed .NET and NuGet commands no longer inherit user-wide caches or configuration. This can make a
first local build download dependencies again, but it removes machine-specific success and avoids
polluting or relying on user state. Upgrades that change Program Kit runtime package pins may now
finish component synchronization with `PKU113`; run the exact restore commands recorded in
`.program-kit/evidence/dotnet-lock-renewal.json`, review the consumer-owned lock changes, and rerun
the updater to prove convergence.

The Keycloak fixture remains local-development-only. Its generated client representation replaces
the unsupported top-level `postLogoutRedirectUris` field with Keycloak's supported
`post.logout.redirect.uris` attribute. No production identity-provider configuration contract is
introduced or changed.

Application authorization remains extensible at the resource and policy-attachment layers. Parsing
provider role/token shapes or the canonical permission claim inside application services is now a
governance violation because that translation belongs to the packaged authentication feature.
