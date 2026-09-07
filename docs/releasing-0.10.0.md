# Releasing Program Kit 0.10.0

This release splits reusable technical building blocks out of Program Kit while advancing the AI
extensions, governance, generators, preset, and workflow to `0.10.0`. Orbyss Foundation and Orbyss
Forms are independently versioned at `0.1.0`; Program Kit no longer owns or publishes their runtime
artifacts.

Before tagging, run the deterministic release gates:

```powershell
./scripts/Test-ProgramKit.ps1 -BrowserEngines 'chromium,webkit'
./scripts/Test-LocalInstall.ps1
python tests/validate_orbyss_building_blocks.py
python tests/validate_nuget_retirement.py
python tests/validate_public_upgrade.py --candidate-dir artifacts
```

Before any stable tag, create the matching GitHub environments and NuGet.org trusted-publishing
policies: `dotnet-foundation/release.yml` with `nuget-production`, `forms/release.yml` with
`forms-packages-production`, and `program-kit/retire-program-kit-nuget.yml` with
`nuget-retirement`. Each environment requires `NUGET_USER`; the retirement policy's unlist scope
must be restricted to `ProgramKit.*`.

Tag and publish Foundation `v0.1.0` first, then Forms `v0.1.0`, waiting for each complete Release
workflow and public NuGet propagation check. Only after both replacement families are public and
verified should Program Kit `v0.10.0` be tagged. The manual retirement workflow remains a separate,
explicitly confirmed operation after all 49 replacement NuGet packages are public.

The clean-consumer acceptance must generate 1.1 intake/map artifacts, review the current draft,
confirm explicitly, and validate in that order. The pricing semantic regression must preserve six
journeys, the four evidence-backed candidate contexts, managed Forms versus consumer semantics, all
typed bridges, and founding decision alternatives. The architecture approval regression must
promote only the reviewed founding ADR bundle.

When explicitly authorized, validate the generated DSL with the exact pinned Structurizr Docker
image and visually inspect the localhost diagrams. Keep Firefox in CI; use Chromium and WebKit for
local browser gates per the repository host limitation.

Create and push the stable tag only from the fully validated and explicitly approved release commit:

```powershell
git tag v0.10.0
git push origin main v0.10.0
```

The complete ordered Release workflow must succeed before consumers are told to install. If the
candidate fails, follow the repository's failed stable-release recovery procedure for the same tag.
