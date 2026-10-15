# Implementation prompt for the release validation follow up

Implement the agreed Program Kit release-validation follow-up in `C:\Users\tech_\Code\program-kit`. The investigation and interview are complete. This is an implementation request: proceed through coding, appropriate validation, committing and a direct push of the follow-up to main. Do not reopen settled policy questions. Resolve routine technical choices yourself; raise only a concrete blocker or a material conflict that the agreed design cannot resolve.

Read these files first:

- `C:\Users\tech_\Code\program-kit\AGENTS.md`
- `C:\Users\tech_\Code\program-kit\docs\reviews\release-validation-follow-up-implementation-plan-2026-10-15.md`
- `C:\Users\tech_\Code\program-kit\docs\reviews\local-release-ci-ownership-audit-2026-10-15.md`
- `C:\Users\tech_\Code\program-kit\docs\reviews\local-release-ci-ownership-checks-2026-10-15.json`

The implementation plan is the detailed file-by-file design and acceptance checklist. The following requirements summarize the user's settled decisions and take precedence over contradictory historical descriptions of the old local gate.

## Verified starting state and isolation

On 15 October 2026 this checkout was switched to main and fast-forwarded to origin/main at `9274d4b4462ef1b1ca70488a7c1d93242cbf3bbc`. Stable v0.13.2 was published at `fff643af3a12b6f7f975106992a792aab2df7cf3`; its complete Release workflow succeeded: https://github.com/orbyss-io/program-kit/actions/runs/38757467458 . The old release hold is satisfied. The only tracked change since audit source `2b21be892719cac1fdcaeb1a9ea1746a1d56c29d` was the published-release README update.

Fetch and inspect current main again before implementation. Preserve new upstream changes. Work in an isolated checkout from current main, using a `codex/` branch if needed, then deliver the follow-up directly to main. Do not change the other chat's worktrees, published tag/assets or historical evidence. No new version, release tag or publication is authorized by this task.

The planning files and this prompt are currently untracked, as is unrelated pre-existing content under `.agents/`. Read/preserve the named handoff documents before creating another checkout and copy only those specific documents if needed there. Do not stage the entire `.agents/` directory, discard untracked files or carry the old diagnostics branch wholesale into main. The audit inventory snapshot is historical, not a candidate qualification receipt. Its recorded raw-file digest must not be relabeled as evidence for a newer checkout; checkout newline conversion can also change raw bytes while Git source content remains identical.

## Required behavior

1. CI owns deterministic release qualification. No mandatory local Release suite repeats CI-capable checks. Local Development and focused debugging checks remain available. A candidate can require no local acceptance execution.
2. Main push CI runs Development plus affected expensive checks and prerequisite closure. Select against the whole push range, with conservative full selection when the base/inputs cannot be established. Preserve PR coverage.
3. Add one complete, untagged candidate qualification workflow. It runs full Linux deterministic acceptance, Chromium/Firefox/WebKit, focused Windows compatibility and security qualification. Reuse an already-successful complete matching qualification. If only partial CI coverage exists, this complete run may repeat some earlier CI checks. Do not implement reuse/merging of individual checks across separate runs in this patch.
4. The focused Windows lane covers real source/packaged installation and upgrades, CMD/Node/npm/Python/uv launchers and PATH, native workflow start/resume and worker permissions/process cleanup. Browser and container integration acceptance stays in Linux CI. Fixture subprocess tests must not start paid coding agents.
5. Build one authoritative publication payload in CI. Linux and Windows package checks consume those exact package bytes. Verify the asset hashes before and after dependent tests; do not let a prerequisite silently rebuild them. An imported verified package set is preparation, not a claim that Windows executed a build it did not run.
6. Tagged Release consumes the previously qualified CI artifact set. It performs exact tag/version/source checks, trusted-run/job/coverage/provenance verification, complete payload/hash verification, security freshness checks, attestation/publication and post-publication public installation/upgrade verification. It never rebuilds packages or invokes the complete deterministic suite.
7. Missing, expired, incomplete, mismatched or untrusted qualification blocks publication with a specific CI recovery instruction. No fallback to a local suite or tests/builds inside tagged Release. An exact older qualified commit can be tagged after main advances; a different tag commit cannot borrow its evidence.
8. Security evidence has a configurable default maximum age of 24 hours. Refresh only the security scan in CI against the unchanged candidate when stale. Keep scan refresh separate from deterministic test qualification and artifact storage retention.
9. Release-oriented optional AI trials download verified CI packages, check actual local prerequisites, prepare a disposable consumer and record separate local preparation/execution evidence. No candidate rebuild or duplicate deterministic acceptance. Preserve individually authorized one-use phases, checkpoint/source/artifact/host/toolchain bindings, workspace-write workers, Windows Job Objects, cleanup/draining, redaction and supervisor-owned credentials. Existing development-learning trials remain separately labeled.
10. Add `.agents/skills/program-kit-release-readiness/SKILL.md` for maintaining Program Kit itself, outside consumer packaging. Use the skill-creator skill to create and validate it. The skill orchestrates deterministic helpers and configurable policy; scripts and CI enforce the gates. It must not grant new paid-worker or publication authority.
11. Readiness assesses the actual changes and recommends relevant optional AI trials, including existing migration/upgrade and continuation phases when applicable. The user chooses trials; publication preparation does not automatically start or require paid runs. Missing scenarios are coverage gaps, not passing evidence.
12. Keep full trial evidence internally. Publish a concise readiness/trial assessment, without automatically uploading full worker logs/checkpoints. Confirmed product defects found by an optional trial block readiness until repaired. Harness failures/inconclusive results receive explicit disposition. No trial run means no AI acceptance claim.

## Integrity details that must survive implementation

- Verify trusted producer repository, workflow revision, event, run and attempt, actual successful required jobs, exact source commit/tree, policy/inventory identity, platform/browser coverage and complete asset inventory. A checksum file supplied beside an artifact is not by itself authenticated provenance.
- Use an acyclic artifact graph: upload payload/file manifest and original validation evidence first; then issue separately authenticated final qualification evidence binding their immutable IDs/digests. The final manifest must not include the enclosing upload digest of itself. Refreshes and readiness assessments reference its stable identity.
- Keep original journals/logs and truthful per-platform observations. Do not rewrite command paths, timestamps or historical receipts to imply another execution.
- Enforce hard failure on integrity mismatches with the actual pinned download implementation. Include every release asset, including release/migration Markdown and referenced profile/evidence files.
- A later applicable failed security scan or unresolved recorded product defect blocks promotion; selecting an older passing scan or assessment cannot conceal it. Define explicit supersession/resolution.
- A trusted workflow recording submitted assessment JSON authenticates the statement's recorder, not the claimed trial execution. Require attributable review, exact candidate binding and references/digests for internally retained trial manifests. Distinguish verified evidence from human-attested findings.
- Publish the concise assessment as supplemental release information; do not edit qualified package bytes or replace hashed assets to append it. Preserve partial-publication handling and exact-commit failed-tag recovery approval. Do not silently clobber differing existing public assets.

## Implementation and validation

Follow the staged plan: policy/schema/verifier; main selection and complete CI qualification; focused Windows/imported package preparation; scan-only refresh and publish-only Release; local preparation and assessment handoff; maintenance skill and aligned commands/docs.

Update AGENTS.md, README, old local Release wrappers, runner/receipt contracts, live schemas/consumers, dependency-maintenance guidance and affected validators coherently. Legacy full-local-Release entry points should give actionable migration guidance, not silently execute a different gate. Preserve historical profiles/evidence and existing consumer locks. Do not undertake unrelated dependency updates. Register any genuinely new external input in maintenance-policy.json.

During development, run focused meaningful tests plus bounded `./scripts/Test-ProgramKit.ps1` Development. Do not run complete local Release, paid acceptance, interactive Start-IntakeSession, or a real publication to validate this patch. Firefox is unavailable on this local Windows host; keep its CI leg and use the documented non-Firefox engines for applicable focused local checks.

Test the plan's failure boundaries, including wrong producer/source/variant, partial coverage, tampered payload plus checksum, missing/expired artifacts, stale/newer-failed security evidence, superseded readiness passes, unchanged tested package bytes, local host identity, authorization boundaries and non-circular manifests. Ensure tagged publication dispatches no full suite or builder. Verify the new skill with its skill-creator validator.

Commit and push only this follow-up directly to main after reviewing/reconciling remote changes. Inspect exact-commit main CI, run one untagged complete qualification for this new mechanism, and exercise its non-publishing promotion verifier against the resulting bundle. Fix failures and qualify the corrected commit. Do not tag or publish a version. If host access, credentials or a real CI limitation blocks completion, preserve evidence and report the exact blocker without weakening the gate or claiming success.

Finish with the implementation summary, commit/main status, relevant successful CI run and artifact identities, validation results, and any remaining limitations. The old full-suite tagged publication must not be considered tested end-to-end merely because a non-publishing verifier passed.
