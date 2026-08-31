---
description: Install or safely update the Program Kit managed .NET repository baseline.
scripts:
  py: scripts/dotnet_sync.py
---

## Input

`$ARGUMENTS` may contain `--check` to report drift without changing files. The repository root is the current
working directory unless an explicit target path is supplied.

## Work

1. Confirm that the approved bootstrap decision register selects .NET and has not explicitly opted out
   of `ProgramKit.Host`. The hash-bound assessment approval plus Accepted bootstrap-baseline decision
   satisfy host/runtime selection and acknowledgement of the pinned preview packages and the
   `CShells Preview` and `Nuplane Preview` NuGet sources. Outside bootstrap, equivalent Accepted ADR
   and explicit acknowledgement evidence are required.
2. For a write, run `{SCRIPT}` with `--target <repository-root> --profile-selected
   --host-runtime-accepted --preview-sources-approved`. Pass a confirmation flag only when its corresponding
   evidence exists. For a read-only drift report, pass `--check --profile-selected`; the two write approvals
   are not required because check mode changes no files.
3. Report created, updated, unchanged, and conflicted files exactly as emitted by the script.
4. Stop on conflicts. Never overwrite a consumer-modified managed file or a scaffold-once consumer file.
5. After a successful write, report that `dotnet restore` and the generated
   `eng/program-kit/Build.ps1 -SkipBundle` access configured package sources. Do not run either command unless
   the user separately authorizes networked package restore and build verification.
6. Make clear that runtime selection is automatic for a .NET bootstrap, while applying the managed
   repository files remains a separate, reviewable synchronization action and is not a prerequisite
   for technology-neutral governance checks. Program Kit bundle updates and repository-baseline
   sync are separate operations.

The sync itself performs local, path-contained file operations and does not contact package feeds. The
generated restore, build, CI, release, and application-bundle paths can access the configured NuGet sources.

The ownership record is `.program-kit/managed.json`. Root MSBuild discovery extension points, application
`VERSION`, and shell configuration are scaffolded once and remain consumer-owned. Program Kit owns the SDK,
NuGet source, analyzer policy, `eng/program-kit`, container, schema, and generated workflow baselines.
