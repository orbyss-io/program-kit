# Releasing Program Kit 0.8.9

This corrective release closes the SPA-PKCE and OpenAPI governance gaps found by the first
PriceCalculator authentication slice. Components are `0.8.9`; changed runtime packages, the
application-neutral host image, and the managed OpenAPI exporter are `0.8.9-preview.1`.

The release makes `.program-kit/spa-pkce.json` the supported typed input for origins, exact redirect
and logout registrations, scopes, renewal timeout, and idle/absolute bounds. Sync derives the
managed host settings, Keycloak fixture, and browser contract. It also removes the BFF secret from
SPA composition, rejects a SPA client secret at host startup, disables authentication evidence
capture, and supplies the local session/cross-tab/logout adapter.

OpenAPI consumers receive managed oasdiff 1.29.1 and generator defaults plus
`eng/program-kit/openapi_init.py`. `toolchain.py --include-openapi` records and rechecks the exact
comparator command; a reviewed binary can be copied into the ignored repository tool directory with
the approval-gated remediation command.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.config
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet run --project tests/dotnet/ProgramKit.DomainEvents.Probe/ProgramKit.DomainEvents.Probe.csproj -c Release --no-build --no-restore
```

The paid live bootstrap and first-slice continuation remain entirely user-invoked. Publication does
not prompt for them or record them as skipped.

## PriceCalculator update and resynchronization

Run these commands from `C:\Code\Orbyss\PriceCalculator` after v0.8.9 is published:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
python .specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py --target . --profile-selected --host-runtime-accepted --preview-sources-approved --persistence-profile none --web-profile spa-pkce
python .specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py --target . --profile-selected --persistence-profile none --web-profile spa-pkce --check
python eng/program-kit/verify_spa_profile.py --repository .
```

The generated default routes already match VS-001. If the application chooses different routes,
edit only `.program-kit/spa-pkce.json`, rerun the write-mode sync command, and then rerun `--check`
and the verifier. Do not edit `hostsettings.json`, the realm, compose file, Playwright configuration,
or browser contract.

For the first public OpenAPI contract, initialize the planned paths rather than constructing the
registry by hand:

```powershell
python eng/program-kit/openapi_init.py --repository . --identity price-calculator-v1 --document-name v1 --shell default --feature <ApiFeatureIdentity> --application-directory <spa-directory> --application-tsconfig <spa-tsconfig>
python eng/program-kit/toolchain.py --repository . --evidence .program-kit/evidence/toolchain.json --include-openapi
python eng/program-kit/js_toolchain.py --repository . npm -- --prefix tools/openapi/price-calculator-v1 install --package-lock-only --ignore-scripts --strict-peer-deps --engine-strict
```

If the pinned comparator is unavailable, download and verify the official oasdiff 1.29.1 binary,
then run the second command with `--remediate --approve --oasdiff-binary <reviewed-binary-path>`.

The remaining legitimate consumer decisions are the SPA OIDC library and its package pin, the
actual SPA source/build directory and Compose overlay, feature-owned permission identities, and the
exact API feature/shell identities supplied to the OpenAPI initializer. These choices may require a
dependency or deployment ADR under the normal thresholds; redirect/session semantics and the
oasdiff choice do not.

Create and push the immutable tag only from the validated release commit:

```powershell
git tag v0.8.9
git push origin main v0.8.9
```
