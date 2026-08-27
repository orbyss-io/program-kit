# Releasing Program Kit 0.4.1

Program Kit `0.4.1` is the Spec Kit bundle version. The .NET packages and host image produced by the same release remain preview artifacts and advance to `0.4.1-preview.1` so the tag never republishes or overwrites the 0.4.0 runtime artifacts.

Complete the one-time GitHub, NuGet trusted-publishing, and GHCR preparation in `docs/releasing-0.4.0.md` before releasing.

## Pre-release verification

From a clean checkout of the release commit, run:

```powershell
uv --system-certs run --with specify-cli==1.0.1 python tests/validate_components.py
uv --system-certs run --with specify-cli==1.0.1 python tests/validate_governance_state.py
uv --system-certs run --with specify-cli==1.0.1 python tests/validate_codex_bootstrap.py
python tests/validate_dotnet_scaffold.py
python tests/validate_dotnet_runtime.py
uv --system-certs run --with specify-cli==1.0.1 specify bundle validate --offline
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet pack ProgramKit.slnx -c Release --no-build
```

Check that `VERSION` is `0.4.1`, `RUNTIME_VERSION` is `0.4.1-preview.1`, and the release commit is on the default branch.

## Create and verify the release

```powershell
git tag -a v0.4.1 -m "Program Kit 0.4.1"
git push origin v0.4.1
```

The tag publishes the three Spec Kit ZIPs plus checksums, the `0.4.1-preview.1` NuGet packages, and the multi-architecture `ghcr.io/orbyss-io/program-kit-host:0.4.1-preview.1` image. Approve protected environment deployments only after verifying the tag points at the reviewed release commit. Verify GitHub attestations, NuGet repository metadata, and the GHCR SBOM/provenance before enabling consumers.
