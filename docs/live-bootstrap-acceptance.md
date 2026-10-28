# Live acceptance v2

Live acceptance v2 is an optional, paid, local diagnostic for a packaged Program Kit candidate. It
does not replace selected deterministic development checks or CI package validation, is never a publication
prerequisite, and must never run in CI or from an unattended hook.

## Retired bootstrap execution

Paid `bootstrap-checkpoint` and `workflow-fresh`, `workflow-failure`, `workflow-resume`
execution is retired. The old entrypoints reject before authorization consumption,
installation, workspace creation or worker dispatch. Use
`$speckit-program-kit-governance-product-intake` to review the founding baseline,
then continue with specification intake. No replacement paid founding trial is supplied.

Historical checkpoints, schemas and receipts remain unchanged and readable. Independent
`building-block-consumer`, feature and upgrade phases retain their exact parent, source,
one-use authorization and verification contracts. An existing valid parent is required;
retirement does not fabricate a new parent or make historical evidence current.

## Candidate preparation

Release-oriented preparation downloads packages from the successful exact-main-commit CI package run via
`scripts/release_candidate.py prepare-trial`. Its separate local `ci-trial-preparation.json`
is selected with `-CiPreparation`; it records actual host/toolchain/install operations,
not a claim that this host executed CI acceptance. Historical `-ReleaseReceipt` records
remain read-only. New preparation binds the clean source, actual local host and toolchains,
CI package-manifest digest, exact package hashes and original preparation logs. The live
harness installs those packages and never builds a candidate itself. Authorization and
execution recheck the source, host, packages and tools. An unavailable historical tool
observation remains unbound, while current live preflight still requires all live tools
to execute and each one-use authorization pins the displayed Codex launcher version.
Firefox acceptance stays in Linux CI; it is unavailable on this local Windows host.

## One-use authorization

A paid phase requires a separately issued, short-lived authorization manifest. The interactive
issuer displays and binds the phase, scenario, candidate receipt, optional parent checkpoint,
exact Codex profile and launcher version, timeout, and paid-session ceiling. It writes a
nonce-bearing manifest only after the
operator types `AUTHORIZE <phase>`. The runner atomically consumes the manifest immediately before
the paid process; it cannot be reused. There is no boolean `-Approved` compatibility path.

For an independently requested building-block diagnostic with an existing valid checkpoint,
issue a new authorization bound to that exact checkpoint:

```powershell
./scripts/New-LiveAcceptanceAuthorization.ps1 `
  -Phase building-block-consumer `
  -CiPreparation artifacts/trial-preparation/<unique>/ci-trial-preparation.json `
  -Checkpoint artifacts/live-acceptance/v2/checkpoints/<checkpoint>.json `
  -Model gpt-5.6-sol `
  -ReasoningEffort high

$env:PROGRAM_KIT_NPM_TOKEN = '<registry token>'
./scripts/Test-LiveBuildingBlockConsumer.ps1 `
  -Authorization artifacts/live-acceptance/v2/authorizations/pending/<authorization>.json `
  -Checkpoint artifacts/live-acceptance/v2/checkpoints/<checkpoint>.json
Remove-Item Env:PROGRAM_KIT_NPM_TOKEN
```

The current catalog uses authenticated GitHub npm publication. The credential belongs only to the
supervisor's registry operations. It is removed from the Codex worker environment, redacted from
captured streams, and is never written to a consumer file or evidence object. Consumer-facing
anonymous distribution remains separate future work.

## Isolation and process ownership

Workers operate only in disposable repositories with `--sandbox workspace-write`. They are told not
to run restores, request credentials, or start browsers, viewers, containers, Java, development
servers, or other unrelated processes. Candidate installation uses temporary loopback catalogs;
the worker's only permitted network purpose is model transport. Registry availability and restore
belong to supervised child processes.

On Windows, every worker process starts suspended, is assigned to a private Job Object configured
with `KILL_ON_JOB_CLOSE`, and resumes only after assignment. Timeout and cancellation terminate the
whole Job. Liveness is determined from process handles and Job accounting—never by sending a console
signal. This avoids the host-closing defect previously caused by POSIX-style signal probing on
Windows. `KeyboardInterrupt` records operator cancellation; exit code 130 without that provenance is
`inconclusive`, not `cancelled`.

While a supervised phase is active on Windows, the harness also holds a scoped
`ES_SYSTEM_REQUIRED` execution-state lease. This prevents idle Modern Standby from suspending a paid
worker or pausing its timeout. The lease is released in `finally` after process-tree cleanup and does
not change the machine's persistent power-plan settings.

The disposable `AGENTS.md` requires command-scoped Git ownership handling:
`git -c safe.directory=<absolute-project> -c core.excludesFile= <command>` on Windows, and
`core.excludesFile=/dev/null` on POSIX. The harness never changes global Git configuration or
weakens the worker sandbox. Python output is forced to UTF-8.

## Evidence and diagnosis

Evidence is retained under `artifacts/live-acceptance/v2/`:

- `objects/sha256/<sha256>` contains content-addressed checkpoint objects and the redacted worker logs;
- `runs/<run-id>/manifest.json` is the schema-validated phase verdict and hash chain;
- `artifacts/live-v2-w/<run-token>/` preserves the disposable consumer at a bounded Windows-safe
  execution path; each run manifest records that relative path;
- `checkpoints/<checkpoint-id>.json` inventories every reusable checkpoint file and hash;
- `authorizations/consumed/` records exactly which one-use authorization was consumed.

The supervisor incrementally redacts secrets across stream chunk boundaries while retaining the
original-stream hash, redaction count, redacted-file hash, cleanup result, and drain result. Failed,
cancelled, and inconclusive runs are evidence and must not be deleted automatically. Failure causes
are classified as preflight, harness, environment, external service, model conformance, product,
operator, or unclassified.

The invoking terminal remains occupied until the authorized phase completes. The full redacted
worker streams are retained in the evidence directory. The final status and restored prompt
are the completion signal; an interrupted or incomplete run is not acceptance.

The old `Test-LiveBootstrap.ps1` and `tests/live/run_bootstrap_acceptance.py` entry points are
retired, as are the v2 paid bootstrap/workflow launch paths. Historical reports remain read-only evidence and are not converted into a new acceptance claim.
