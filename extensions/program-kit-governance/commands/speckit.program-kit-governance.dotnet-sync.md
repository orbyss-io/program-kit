---
description: Install or safely update the Program Kit managed .NET repository baseline.
---

## Input

`$ARGUMENTS` may contain `--check` to report drift without changing files. The repository root is the current
working directory unless an explicit target path is supplied.

## Work

1. Confirm that the accepted technology profile selects .NET and that repository-scaffolding work is authorized.
2. Run the installed extension script `scripts/dotnet_sync.py` with `--target <repository-root>
   --profile-selected`. Pass `--check` when requested. Never pass `--profile-selected` unless the repository's
   accepted technology-profile evidence selects .NET.
3. Report created, updated, unchanged, and conflicted files exactly as emitted by the script.
4. Stop on conflicts. Never overwrite a consumer-modified managed file or a scaffold-once consumer file.
5. After a successful write, run `dotnet restore` and the generated
   `eng/program-kit/Build.ps1 -SkipBundle` when the .NET SDK is available.
6. Remind the user that Program Kit bundle updates and repository-baseline sync are separate, reviewable actions.

The ownership record is `.program-kit/managed.json`. Root MSBuild discovery extension points, application
`VERSION`, and shell configuration are scaffolded once and remain consumer-owned. Program Kit owns the SDK,
NuGet source, analyzer policy, `eng/program-kit`, container, schema, and generated workflow baselines.
