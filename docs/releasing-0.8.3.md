# Releasing Program Kit 0.8.3

This corrective patch synchronizes the public installation and upgrade assertions with the
33-step bootstrap workflow shipped in 0.8.2. Components are `0.8.3`; runtime packages and the
shallow host image are `0.8.3-preview.1`.

Before tagging:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
dotnet restore ProgramKit.slnx --locked-mode
dotnet build ProgramKit.slnx -c Release --no-restore
python tests/validate_dotnet_feature_host.py
python tests/validate_public_install.py
python tests/validate_public_upgrade.py
```

Before publishing, ask the user whether to run the paid live bootstrap acceptance suite. If the
answer is yes, run `./scripts/Test-LiveBootstrap.ps1 -Integration codex -Approved`, inspect its
preserved report and both output streams, and stop the release if it fails. If the answer is no,
record that explicit skip in the release handoff. Never run this suite in CI.

The 0.8.2 assets installed correctly, but its release job failed after publication because the
post-publication assertion still listed the older 25-step workflow. Do not move or replace that
immutable tag. Publish this correction under `v0.8.3` and require both public tests to pass.

Existing consumers upgrade in this order:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
python .specify/extensions/program-kit-governance/scripts/ensure_utf8.py --target .
```

Replace `codex` with the repository integration.

```powershell
git tag v0.8.3
git push origin main v0.8.3
```
