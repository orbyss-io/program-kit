# Releasing Program Kit 0.8.2

This patch release adds a validated normalized-design intake, compact hash-bound bootstrap context,
proportional artifact budgets, and the explicitly approved local-only live bootstrap acceptance
suite. Components are `0.8.2`; runtime packages and the shallow host image are `0.8.2-preview.1`.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
python tests/validate_dotnet_feature_host.py
```

Before publishing, ask the user whether to run the paid live bootstrap acceptance suite. If the
answer is yes, run `./scripts/Test-LiveBootstrap.ps1 -Integration codex -Approved`, inspect its
preserved report and both output streams, and stop the release if it fails. If the answer is no,
record that explicit skip in the release handoff. Never run this suite in CI.

For Codex on Windows, the harness supplies `workspace-write` and disposable worker instructions.
If Git reports dubious ownership, use the command-scoped
`git -c safe.directory=<absolute-disposable-project> -c
core.excludesFile=<platform-null-device> <command>` form inside that run. The second override avoids
warnings when the sandbox cannot read the user's ignore file. Do not change global Git
configuration or bypass the sandbox. The harness also establishes UTF-8 and preserves raw worker
output in the evidence directory while showing concise progress. See
[`live-bootstrap-acceptance.md`](live-bootstrap-acceptance.md) for the complete operating contract.

Verify that all release checksums pass and that a clean disposable consumer installs the normalized
brief command, context schemas, workflow, validators, and runtime components from the packaged
candidate. The live suite is an explicit pre-publication choice rather than a CI job.

Existing consumers upgrade and synchronize in this order:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
python .specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py --target . --profile-selected --host-runtime-accepted --preview-sources-approved
```

Replace `codex` with the repository integration. Add web/persistence profile flags only when Accepted
evidence selects them. Review consumer-owned `hostsettings.json`, `shells.json`, and customized
Dockerfiles.

```powershell
git tag v0.8.2
git push origin main v0.8.2
```
