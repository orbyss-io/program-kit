# Legacy ProgramKit NuGet compatibility

The published `ProgramKit.*` packages are legacy component identities. Their replacements are the
independently versioned `Orbyss.Foundation.*`, `Orbyss.Forms.*`, and `Orbyss.Localization.*`
families. Program Kit itself remains an AI extension and does not publish a NuGet runtime.

Program Kit and generated consumers must never remove, hide, or otherwise mutate any legacy
package version. The immutable legacy IDs remain available for existing consumers and exact-version
restore. Migration to the replacement package families is an explicit consumer source change.

The read-only inventory is
`operations/nuget/legacy-programkit-package-inventory.json`: 49 package IDs and 213 published
versions, queried from NuGet.org on 2026-09-07. The compatibility gate verifies that inventory and
also verifies that all 22 Foundation packages at `0.1.0`, all 15 Forms packages at `0.1.1`, and all
13 Localization packages at `0.1.1` are public and listed.

Run the read-only public compatibility check with:

```powershell
python scripts/verify_legacy_programkit_nuget.py --verify-public
```

This command performs HTTP reads only. It accepts no registry credential and exposes no mutation
mode. Any future package-lifecycle proposal would require a separate architecture decision outside
Program Kit; it must not be introduced through validation, release, bootstrap, or consumer tooling.
