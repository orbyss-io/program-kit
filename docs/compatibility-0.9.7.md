# Program Kit 0.9.7 compatibility report

0.9.7 is a compatible updater, feature-composition, and local-authentication correction over 0.9.6.
Components are `0.9.7`; runtime packages and the host image advance to `0.9.7-preview.1`.

Existing feature packages that set `ProgramKitFeatureIdentity` must now declare the same exact,
case-sensitive value in `[ShellFeature("...")]`. This closes the gap between MSBuild/package
metadata, the CShells runtime catalog, `shells.json`, and OpenAPI export. Packages already following
that contract require no source change. A mismatch is a build-time `PK1006` error and also fails
closed at runtime or export rather than silently omitting the feature.

`ProgramKitWebOptions` adds the optional `BackchannelAuthority`. `Authority` remains the public OIDC
issuer and browser-facing authority. The managed Compose topology sets only the backchannel value
for the application container, joins application and Keycloak to `program-kit-local`, and uses
Keycloak's dynamic backchannel support. Consumer overlays must not restore the removed
`localhost:host-gateway` override.

The offline updater remains command-compatible. In the specific Windows Codex sandbox case where a
uv `specify.exe` is readable but its embedded Python cannot execute, the updater validates and uses
the same installed `specify_cli` site-packages through its own Python process. It downloads and
persists nothing; incompatible environments still stop before mutation with `PKU114` and an exact
normal-PowerShell retry command.

Managed authenticated-web repositories receive the corrected persona-fixture path and a pre-browser
fixture-load regression. Existing consumer-owned web code and authentication response contracts are
unchanged.
