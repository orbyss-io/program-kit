# Releasing Program Kit 0.4.0

Program Kit `0.4.0` is the Spec Kit bundle version. The .NET packages and host image produced by the same
release are intentionally preview artifacts at `0.4.0-preview.1`.

## One-time GitHub preparation

1. Merge the implementation into the repository's default branch only after all required checks pass.
2. In **Settings → Actions → General**, permit GitHub Actions to read and write repository contents and
   packages. Keep fork pull-request workflows read-only and approval-gated.
3. In **Settings → Environments**, create `nuget-production` and `host-production`:
   - add the maintainers who may approve registry publication as required reviewers to both;
   - restrict deployment tags to `v*.*.*` in both;
   - add the environment secret `NUGET_API_KEY` to `nuget-production` after creating the scoped NuGet.org API key.
4. Scope the NuGet.org API key to new package IDs `ProgramKit.Tasks.Abstractions`, `ProgramKit.Tasks`, and
   `ProgramKit.Analyzers`, with push permission and the shortest practical expiry. Do not give it unlist or
   ownership-management permissions.
5. Confirm the organization permits this repository to create packages in GitHub Container Registry. The
   host workflow uses the repository `GITHUB_TOKEN`; no personal access token is required.

The NuGet workflow deliberately builds and attests packages but skips the push when `NUGET_API_KEY` is absent.
This makes it safe to merge before the authentication policy is supplied, but the first release is not complete
until the secret is configured and all three package IDs are visible on NuGet.org.

## Pre-release verification

From a clean checkout of the release commit, run:

```powershell
uv --system-certs run --with specify-cli==1.0.1 python tests/validate_components.py
uv --system-certs run --with specify-cli==1.0.1 python tests/validate_governance_state.py
python tests/validate_dotnet_scaffold.py
python tests/validate_dotnet_runtime.py
uv --system-certs run --with specify-cli==1.0.1 specify bundle validate --offline
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet pack ProgramKit.slnx -c Release --no-build
```

Check that `VERSION` is `0.4.0`, `RUNTIME_VERSION` is `0.4.0-preview.1`, and the release commit is on the
default branch.

## Create the release

Create and push the tag only after GitHub preparation and pre-release verification:

```powershell
git tag -a v0.4.0 -m "Program Kit 0.4.0"
git push origin v0.4.0
```

That single tag starts three independent workflows:

- **Release** publishes and attests the Spec Kit bundle, extension, workflow, and checksums.
- **Publish Program Kit NuGet Packages** publishes and attests the three `0.4.0-preview.1` packages through
  the protected `nuget-production` environment.
- **Publish Program Kit Host Image** publishes a multi-architecture, SBOM- and provenance-bearing image as
  `ghcr.io/orbyss-io/program-kit-host:0.4.0-preview.1` and `:sha-<commit>`.

Approve the NuGet and host-image environment deployments only after verifying the tag points at the reviewed release commit. Do not rerun a partially failed release blindly; inspect which
registries already accepted immutable artifacts. The NuGet push is duplicate-safe.

## Verify and enable consumers

1. Verify the GitHub release contains the three Spec Kit ZIPs and `SHA256SUMS`, and that its attestations verify.
2. Verify all three NuGet packages are `0.4.0-preview.1` and expose their repository metadata.
3. Verify the GHCR host image has both `linux/amd64` and `linux/arm64` manifests, an SBOM, and provenance.
4. Make the host package public so unauthenticated Docker, Kubernetes, and Azure deployments can pull it. If it
   must remain private, grant each consumer repository explicit Actions access to the package instead.
5. Resolve the host image digest and set each consuming repository's Actions variable `PROGRAMKIT_HOST_IMAGE`
   to `ghcr.io/orbyss-io/program-kit-host@sha256:<digest>`. Never configure a mutable tag there.

Consumers then install/update the Program Kit Spec Kit bundle, explicitly select the .NET profile, and run
`speckit.program-kit-governance.dotnet-sync`. Their application tag workflow publishes
`application-bundle.zip`; when `PROGRAMKIT_HOST_IMAGE` is configured, it also publishes the thin layered
application image.
