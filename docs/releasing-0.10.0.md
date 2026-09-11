# Releasing Program Kit 0.10.0

This release splits reusable technical building blocks out of Program Kit while advancing the AI
extensions, governance, generators, preset, and workflow to `0.10.0`. Orbyss Foundation is pinned at
`0.1.0`; Orbyss Forms and Orbyss Localization are pinned independently at `0.1.1`. Program Kit no
longer owns or publishes their runtime artifacts.

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
`artifacts/release-validation-0.10.0.log` plus the machine-bound
`artifacts/release-receipt-0.10.0.json` for later inspection and does not run an optional paid
Codex-worker phase.

Before the Program Kit stable tag, verify the already-published component releases and public package
propagation: `dotnet-foundation` `v0.1.0`, `forms` `v0.1.1`, and `localization` `v0.1.1`.

Only after all three replacement families and the 12 Forms npm packages are public and verified
should Program Kit `v0.10.0` be tagged. Legacy `ProgramKit.*` handling is permanently read-only:
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
git tag v0.10.0
git push origin main v0.10.0
```

The complete ordered Release workflow must succeed before consumers are told to install. If the
candidate fails, follow the repository's failed stable-release recovery procedure for the same tag.
