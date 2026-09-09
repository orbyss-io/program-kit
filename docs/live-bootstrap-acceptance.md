# Live acceptance v2

Live acceptance v2 is an optional, paid, local diagnostic for a packaged Program Kit candidate. It
does not replace the deterministic Development or Release suites, is never a publication
prerequisite, and must never run in CI or from an unattended hook.

The protocol separates bootstrap from later diagnostics. A successfully bootstrapped consumer is
sealed as a content-addressed checkpoint; every additional phase starts from a verified copy of
that checkpoint. Repeating a building-block diagnostic therefore does not repeat the paid bootstrap.

## Implemented phases

The first v2 scenario is `internal-forms-workspace` v1. Its bootstrap fixture describes an internal
forms workspace with an API, BFF, Forms integration, React frontend, shared shell, Foundation host,
and root solution. The scenario and its deterministic expectation bind the architecture decisions,
catalog resolution hash, 18 Program Kit-selected artifacts, 10 shell activations, six BFF
configuration records, exact consumer-owned npm dependencies, and a non-Orbyss `Microsoft.OpenApi`
NuGet sentinel.

Two independently authorized phases are implemented:

1. `bootstrap-checkpoint` installs the exact Release candidate, runs the real bootstrap workflow,
   validates the result, binds the already-reviewed building-block selection, and seals a reusable
   checkpoint.
2. `building-block-consumer` copies that checkpoint, runs one Codex session to plan and apply the
   accepted building blocks and emit a credential-free restore request, then lets the supervisor
   verify selected public availability, perform renew and locked restores, build, run the npm
   verification, apply the deterministic oracle, and seal a derived checkpoint.

This is deliberately not a full feature vertical slice. A future Speckit lifecycle diagnostic can
consume the same bootstrap checkpoint without changing or rerunning the bootstrap phase. Arbitrary
existing-consumer intake, other agent providers, and POSIX qualification are also follow-up scope.

## Candidate receipt

The complete deterministic Release suite creates
`artifacts/release-receipt-<version>.json`. The receipt binds the clean Git commit and tree,
platform and observed toolchains, successful Release steps, browser engines, catalog and
public-availability hashes,
and the exact current-version release artifacts. The live harness installs those artifacts and
never builds a candidate itself. A phase refuses the receipt if the source commit, platform, or any
toolchain actually observed by Release has changed. An `unavailable` receipt value is explicitly
unbound: the live preflight still requires every live tool to execute successfully, and the one-use
authorization independently pins the exact Codex launcher version shown to the operator.

On this Windows host, run Release only after the candidate has been approved for publication and
from a normal user-owned terminal:

```powershell
./scripts/Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Firefox remains in CI and is the authority for that browser leg.

## One-use authorization

A paid phase requires a separately issued, short-lived authorization manifest. The interactive
issuer displays and binds the phase, scenario, candidate receipt, optional parent checkpoint,
exact Codex profile and launcher version, timeout, and paid-session ceiling. It writes a
nonce-bearing manifest only after the
operator types `AUTHORIZE <phase>`. The runner atomically consumes the manifest immediately before
the paid process; it cannot be reused. There is no boolean `-Approved` compatibility path.

Issue and run a bootstrap checkpoint:

```powershell
./scripts/New-LiveAcceptanceAuthorization.ps1 `
  -Phase bootstrap-checkpoint `
  -ReleaseReceipt artifacts/release-receipt-0.10.0.json `
  -Model gpt-5.6-sol `
  -ReasoningEffort high

./scripts/New-LiveBootstrapCheckpoint.ps1 `
  -Authorization artifacts/live-acceptance/v2/authorizations/pending/<authorization>.json
```

The run report prints the sealed checkpoint path. Issue a new authorization bound to that exact
checkpoint, then run the single-session building-block consumer phase:

```powershell
./scripts/New-LiveAcceptanceAuthorization.ps1 `
  -Phase building-block-consumer `
  -ReleaseReceipt artifacts/release-receipt-0.10.0.json `
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

The disposable `AGENTS.md` requires command-scoped Git ownership handling:
`git -c safe.directory=<absolute-project> -c core.excludesFile= <command>` on Windows, and
`core.excludesFile=/dev/null` on POSIX. The harness never changes global Git configuration or
weakens the worker sandbox. Python output is forced to UTF-8.

## Evidence and diagnosis

Evidence is retained under `artifacts/live-acceptance/v2/`:

- `objects/sha256/<sha256>` contains content-addressed checkpoint objects and the redacted worker logs;
- `runs/<run-id>/manifest.json` is the schema-validated phase verdict and hash chain;
- `runs/<run-id>/workspace/` preserves the disposable consumer for troubleshooting;
- `checkpoints/<checkpoint-id>.json` inventories every reusable checkpoint file and hash;
- `authorizations/consumed/` records exactly which one-use authorization was consumed.

The supervisor incrementally redacts secrets across stream chunk boundaries while retaining the
original-stream hash, redaction count, redacted-file hash, cleanup result, and drain result. Failed,
cancelled, and inconclusive runs are evidence and must not be deleted automatically. Failure causes
are classified as preflight, harness, environment, external service, model conformance, product,
operator, or unclassified.

The old `Test-LiveBootstrap.ps1` and `tests/live/run_bootstrap_acceptance.py` entry points are
retired. Historical v1 reports remain read-only evidence and are not converted or treated as v2.
