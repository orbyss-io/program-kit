# Releasing Program Kit 0.4.3

Program Kit `0.4.3` is the Spec Kit bundle version. The .NET packages and host image produced by
the same release advance to `0.4.3-preview.1` so the tag never republishes or overwrites the 0.4.2
runtime artifacts.

Complete the one-time GitHub, NuGet trusted-publishing, and GHCR preparation in
`docs/releasing-0.4.0.md` before releasing.

## Pre-release verification

From a clean checkout of the release commit, run:

```powershell
uv --system-certs run --with specify-cli==1.0.1 python tests/validate_components.py
uv --system-certs run --with specify-cli==1.0.1 python tests/validate_governance_state.py
uv --system-certs run --with specify-cli==1.0.1 python tests/validate_codex_bootstrap.py
python tests/validate_dotnet_scaffold.py
python tests/validate_dotnet_runtime.py
uv --system-certs run --with specify-cli==1.0.1 specify bundle validate --offline
python scripts/build_release.py
python tests/validate_release_install.py
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
dotnet pack ProgramKit.slnx -c Release --no-build
```

The Codex bootstrap and packaged-install tests must confirm that no `.rules` file or positive
outside-sandbox/approval guidance is present in the release assets, and that the installed skill and
reference direct the human to a normal user-owned shell.

Check that `VERSION` is `0.4.3`, `RUNTIME_VERSION` is `0.4.3-preview.1`, and the release commit is on
the default branch.

## Create and verify the release

```powershell
git tag -a v0.4.3 -m "Program Kit 0.4.3"
git push origin v0.4.3
```

The tag triggers the repository's existing GitHub release, NuGet, and host-image workflows. They
publish the three Spec Kit ZIPs plus checksums, the `0.4.3-preview.1` NuGet packages, and the
multi-architecture `ghcr.io/orbyss-io/program-kit-host:0.4.3-preview.1` image. Do not publish these
artifacts manually. Verify that the tag workflows were created; continuous polling is unnecessary
unless a workflow reports that intervention is needed.
