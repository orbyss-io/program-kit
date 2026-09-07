# ProgramKit NuGet package retirement

The published `ProgramKit.*` packages are legacy component identities. Their replacements are the
independently versioned `Orbyss.Foundation.*`, `Orbyss.Forms.*`, and `Orbyss.Localization.*`
families. Program Kit itself remains an AI extension and does not publish a NuGet runtime.

NuGet.org does not permanently delete ordinary packages. Its delete command unlists an exact
package version: new consumers no longer discover it in normal search, while existing consumers can
still restore the exact version. The immutable IDs therefore remain reserved and recoverable.

The exact retirement inventory is `operations/nuget/program-kit-retirement.json`: 49 package IDs
and 213 published versions, queried from NuGet.org on 2026-09-07. The operation is deliberately
gated. Before it mutates NuGet.org, it verifies that all 22 Foundation and 27 Forms/Localization
replacement packages at version 0.1.0 are public.

## One-time trusted-publishing policy

Create a NuGet.org trusted-publishing policy with the unlist scope restricted to `ProgramKit.*`:

- Repository owner: `orbyss-io`
- Repository: `program-kit`
- Workflow file: `retire-program-kit-nuget.yml`
- Environment: `nuget-retirement`

Create the matching GitHub environment and define its `NUGET_USER` variable as the NuGet.org profile
name. Required reviewers are recommended because one run unlists the entire legacy family.

After both replacement release workflows have succeeded and public propagation is verified, manually
run **Retire ProgramKit NuGet packages** and enter the exact confirmation shown by the workflow. Do
not run it from a tag or add it to the normal Program Kit release graph.

For a local, non-mutating audit:

```powershell
python scripts/retire_programkit_nuget.py --verify-public
```

The executing form additionally requires an unlist-scoped `NUGET_API_KEY` and the exact confirmation.
Do not store that key in the repository or print it in logs.
