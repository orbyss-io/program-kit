# Releasing Program Kit 0.12.0

This candidate adds the public `speckit.program-kit-governance.sync` coordinator for repository
setup, planning package context, implementation materialization and offline upgrade. The old
`speckit.program-kit-dotnet.sync` command is retired without an alias. Its internal engineering
adapter remains behind the coordinator. Upgrade protects consumer edits before retiring integrations.

Exact npm metadata, graph and restore operations share catalog routing, runtime and trust context.
Phase readiness distinguishes planned targets, existing skeletons and current locked restore proof.
Changed inputs invalidate evidence; unchanged graphs and completed restore subjects can be reused.
The optional staged live comparison uses one confirmed authorization per paid stage and explicit
human feature-intake confirmation. See [repository sync validation](repository-sync-implementation.md).
This document is preparation guidance, not a claim that 0.12.0 has been published or live-accepted.

All Program Kit installable components advance together to `0.12.0`. Orbyss Foundation remains
pinned at `0.2.2`; Forms is pinned at `0.2.0` and Localization at `0.1.1`. This minor version publishes no runtime
component versions.

Before tagging, establish successful deterministic local Release evidence:

Commit the final candidate first and verify a clean working tree. The receipt binds the exact source
commit/tree and candidate assets; a dirty tree cannot produce a successful receipt. Inspect the
preserved transcript and receipt before preparing the approved publication commit/tag. Keep all
human evaluation transcripts and disposable consumers in ignored local artifacts, outside the PR.

A different commit SHA alone does not require another local Release run or a new local receipt.
For test-only corrections, non-shipped contributor/release documentation, or CI-only validation
changes that preserve or add coverage without changing build/packaging/publication behavior, follow
[Reusing local Release evidence after non-shipping changes](../AGENTS.md#reusing-local-release-evidence-after-non-shipping-changes).
Verify the original receipt/log and artifact hashes, review the entire diff against actual packaging
inputs, preserve gate coverage, run relevant targeted checks, and require green CI on the latest
candidate. Record both commit IDs and the evidence for unchanged shipped content/build inputs in
the PR. A test's cross-platform shell-discovery fix is an example; changing an installed skill or
generator is not. If unchanged payloads cannot be established, obtain fresh local Release evidence.

Preserve the original receipt unchanged; never regenerate it alone or relabel it for the new commit.
The tagged Release workflow still runs in full and generates its own exact-commit receipt. This
evidence-reuse exception does not relax paid live-acceptance receipt checks. It also applies to
failed-tag recovery only when the failure is a demonstrated test/assertion or CI-only validation defect,
not a product failure, and nothing was published from the failed candidate. Preserve the failed run
evidence and verify publication steps, release assets and immutable registry artifacts; record the
diagnosis, complete diff, original and corrected commits, artifact hash verification, targeted checks
and green CI for the latest candidate. Exact corrected-commit and same-tag approval is still required
before moving a failed tag. If any reuse condition is unproven, obtain fresh local Release evidence.
The command below is needed for the initial gate or a material candidate
change, not merely to refresh a SHA after an eligible non-shipping correction.

```powershell
./scripts/Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Run this complete suite from a normal user-owned terminal only after the user has decided the
candidate should proceed toward publication. It includes the source validators, Chromium/WebKit,
release build, packaged-install checks, previous-release upgrade, disposable local installation, and
the read-only public component-package gate. It writes
`artifacts/release-validation-0.12.0.log` plus the machine-bound
`artifacts/release-receipt-0.12.0.json` for later inspection and does not run an optional paid
Codex-worker phase.

Local, PR CI and tagged Release select checks from `tests/validation-inventory.json`.
The shared runner records each check's command, result, timestamps and hashed log under
`artifacts/validation-runs/<run>/`; failed runs retain that evidence. Independent checks
continue after a failure, while dependents are marked blocked. Existing version transcripts
are archived before a new run. Receipt generation requires complete successful inventory
coverage for the current platform, source, browser engines and artifact set.

The inventory includes the published-host and Forms renderer integration probes. Registry
checks require `PROGRAM_KIT_NPM_TOKEN` in the invoking terminal; it is passed only to checks
declaring that need, and evidence is redacted. Browser provisioning precedes checks which
consume it. The pinned host image is pulled explicitly rather than assumed to be cached.
No host TLS-monitoring setting is removed by validation.

`validate_installed_bootstrap_flow.py` runs the complete packaged workflow with real shell
validators and explicitly fictional authoring/review decisions. It covers ordinary completion,
owned implementation deferrals, discovery before specification, and retry after malformed
producer output. Open obligations remain enforced after bootstrap completion. This establishes
mechanical composition; it is not evidence of live-agent reasoning quality. The older packaged
consistency test remains a focused terminal-governance regression.

For one targeted check, use `python scripts/run_validation.py --check <inventory-id>`.
This produces check evidence but cannot produce a Release receipt. Windows installation and
mixed-interpreter checks have an explicit CI lane; Firefox remains required in Linux CI.

Before the Program Kit stable tag, verify the component tags and published package/image
propagation (a GitHub Release entry is not required for each component): `dotnet-foundation` `v0.2.2`, `forms` `v0.2.0`, and `localization` `v0.1.1`.

Only after all three replacement families and all cataloged Forms npm packages are public and verified
should Program Kit `v0.12.0` be tagged. Legacy `ProgramKit.*` handling is permanently read-only:
Program Kit records and verifies compatibility, but neither release tooling nor consumer tooling may
remove, hide, or otherwise mutate those package versions.

The clean-consumer acceptance must generate 1.1 intake/map artifacts, review the current draft,
confirm explicitly, and validate in that order. The pricing semantic regression must preserve six
journeys, the four evidence-backed candidate contexts, managed Forms versus consumer semantics, all
typed bridges, and founding decision alternatives. The architecture approval regression must
promote only the reviewed founding ADR bundle.

When explicitly authorized, validate the generated DSL with the exact pinned Structurizr Docker
image and visually inspect the localhost diagrams. Keep Firefox in CI; use Chromium and WebKit for
local browser gates per the repository host limitation.

Create and push the stable tag only from the fully validated and explicitly approved release commit:

```powershell
git tag v0.12.0
git push origin main v0.12.0
```

The complete ordered Release workflow must succeed before consumers are told to install. If the
candidate fails, follow the repository's failed stable-release recovery procedure for the same tag.
