# Program Kit 0.9.6 compatibility report

0.9.6 is a consumer-tooling correction over 0.9.5. It does not change the packaged authentication,
web-feature, task, or domain-event APIs. Runtime packages and the host image advance to
`0.9.6-preview.1` so consumers can upgrade through the normal immutable package path.

Managed repositories gain `eng/program-kit/Restore.ps1`. Use it instead of invoking `dotnet restore`
directly when the restore is part of a governed Program Kit build or lock renewal. Existing
consumer-owned aggregate verification remains supported: the managed
`Invoke-RepositoryVerification.ps1` establishes the repository-owned environment before calling
`eng/verify.ps1`.

Application `VERSION` remains consumer-owned application provenance. Runtime-closure evidence is now
validated against the separate installed Program Kit version, so applications are neither expected
nor permitted to align their own version with Program Kit.

The Git correction is command-scoped. It does not create a global `safe.directory` entry, use
`safe.directory=*`, or bypass repository-owner validation for unrelated repositories.
