# Releasing Program Kit 0.8.1

This patch release corrects the runtime boundary of the withdrawn 0.8.0 release. Components are `0.8.1`;
runtime packages and the shallow host image are `0.8.1-preview.1`.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
python tests/validate_dotnet_feature_host.py
```

The paid live bootstrap acceptance suite is optional and user-invoked. Do not prompt for it during
publication or record it as skipped. If the user explicitly requests the run, use
`./scripts/Test-LiveBootstrap.ps1 -Integration codex -Approved`, inspect its preserved report and
both output streams, and repair any in-scope failure before reporting the result. Never run this
suite in CI.

For Codex on Windows, the harness supplies `workspace-write` and disposable worker instructions.
If Git reports dubious ownership, use the command-scoped
`git -c safe.directory=<absolute-disposable-project> -c core.excludesFile= <command>` form on
Windows (or `/dev/null` on POSIX) inside that run. The second override avoids
warnings when the sandbox cannot read the user's ignore file. Do not change global Git
configuration or bypass the sandbox. The harness also establishes UTF-8 and preserves raw worker
output in the evidence directory while showing concise progress. See
[`live-bootstrap-acceptance.md`](live-bootstrap-acceptance.md) for the complete operating contract.

Verify that host source/package references contain only Nuplane/CShells plumbing, all seven release
checksums pass, and the disposable consumer feature activates from a staged runnable-host directory without
a bundle parser or host health endpoint.

Existing consumers upgrade and synchronize in this order:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
python .specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py --target . --profile-selected --host-runtime-accepted --preview-sources-approved
```

Replace `codex` with the repository integration. Add web/persistence profile flags only when Accepted
evidence selects them. Review consumer-owned `hostsettings.json`, `shells.json`, and customized Dockerfiles.

```powershell
git tag v0.8.1
git push origin main v0.8.1
```
