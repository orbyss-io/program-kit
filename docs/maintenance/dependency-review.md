# Automatic dependency updates

Run this repository's **Update dependencies** workflow before preparing a release,
or start it manually for an upstream update. It also runs weekly. This is repository
maintenance; ordinary Spec Kit commands and implementation checkpoints do not run it.

The workflow discovers publisher versions, upgrades active tools, packages, actions
and image digests, refreshes native locks, prepares and qualifies a new public
dependency profile, captures its exact package schemas, interfaces and frozen source
guidance, and promotes that passing profile and knowledge together. Historical
profiles and existing consumer locks remain available.

All deterministic checks and image vulnerability scans must pass before the job
opens an update PR. Failed lookups or incompatible contracts stop the job and preserve
diagnostics. Fix the failure and rerun; there are no per-dependency decision forms.

New external inputs belong in maintenance-policy.json. Foundation has its own
independent workflow and publishes knowledge with each release. Program Kit adopts
public releases: editing Foundation source does not change a published package or
image. Run Foundation's update first when its contracts need upgrading, then rerun
Program Kit after publication.

For local development run `python scripts/update_dependencies.py --development`.
Complete update validation runs in Linux CI, including Firefox. Local Windows
Release validation retains the contributor instructions in AGENTS.md. Publication
still uses the tagged Release workflow.

Sources: [.NET image maintenance](https://github.com/dotnet/dotnet-docker/blob/main/documentation/vulnerability-reporting.md),
[Dependabot configuration](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference),
[Trivy scanning](https://trivy.dev/docs/dev/guide/scanner/vulnerability/).
