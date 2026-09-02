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
