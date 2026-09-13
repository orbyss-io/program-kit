# Equipment Lending Desk: full intake and first slice trial

This fictional mixed-stack product exercises policies, lifecycle transitions,
durable operation identity, extension boundaries, released Foundation/Forms
mechanisms, repository sync and browser behavior together. The fixed HTTP/browser
contracts make independent verification possible. They are visible requirements,
not product implementation supplied to the agent.

## Candidate and real intake

Finish targeted and bounded Development validation, freeze the candidate on the
separate implementation branch, then prepare an exact development trial receipt:

```powershell
python tests/live/v2/trial_candidate.py --source-root . --validation-python C:\Tools\uv\tools\specify-cli\Scripts\python.exe
```

This performs component/schema/package/install preparation only. It starts no
coding agent and is not Release validation. Preserve its printed receipt path.
Do not change candidate source during the experiment; a changed candidate needs
fresh preparation and phase authorization.

The **human** starts the following in a normal foreground terminal at the candidate
worktree. Normal interactive model usage applies. Do not run this interactive mode
from an agent, CI or an unattended hook.

```powershell
.\scripts\Start-IntakeSession.ps1 -KeepWorkspace `
  -IdeaFile tests\live\scenarios\knowledge-application\v1\PROJECT_REQUEST.md `
  -AcceptanceContracts tests\live\scenarios\knowledge-application\v1\bootstrap-seed\fixture\acceptance
```

The installed Program Kit skill conducts the actual interview. It starts from
the product request and observable contracts, without prepared architectural
decisions or confirmation. Review its artifacts and confirm only when satisfied.
Exit with `/quit` after the intake handoff. The launcher does not start bootstrap.
Keep the printed evidence directory, archive and conversation for review.

`-PrepareOnly` exercises the same installer and evidence capture without starting
an agent. Its output is setup evidence and cannot be admitted as an actual intake.

After reviewing the real conversation, capture its confirmed inputs:

```powershell
python tests/capture_lending_intake.py --session <intake-evidence-directory> --output <new-captured-scenario-directory>
```

If the intake contains multiple founding decisions, supply the exact relevant
reviewed IDs with repeated `--decision-id` arguments. Capture preserves confirmed
input bytes, validates them through the native validator and binds their original
session/archive/transcript. It supplies no bootstrap or feature approval. A changed
product or fixed contract requires revising and reviewing the fixture; capture
must not silently transform the human's accepted intent to fit this oracle.

The tracked `bootstrap-seed/fixture/docs/architecture` is a **synthetic input for
deterministic tests**. The full human trial uses the captured scenario instead.

## Bootstrap and first vertical slice

Issue bootstrap authorization only after capture, with the reviewed model,
reasoning, timeout and the exact trial receipt. Use the captured path as `-Scenario`:

```powershell
.\scripts\New-LiveAcceptanceAuthorization.ps1 -Phase bootstrap-checkpoint `
  -TrialReceipt <trial-receipt> -Scenario <captured-scenario-directory> `
  -Model <reviewed-model> -ReasoningEffort <reviewed-effort>
```

The foreground prompt shows the exact paid-session limit and requires the literal
`AUTHORIZE bootstrap-checkpoint`. The user returns the resulting one-use manifest.
The agent may then run `New-LiveBootstrapCheckpoint.ps1` with that manifest and the
same scenario. Inspect every generated result, including a failed or incomplete
run, before continuing. A rerun always needs a fresh authorization.

Successful bootstrap carries the captured scenario path into these separately
authorized `fresh-candidate` phases through their exact parent checkpoints:

1. `feature-intake`: produce the RM01 review; stop for actual human confirmation.
2. Seal that confirmation with `cli.py confirm-sync-intake`, using the reviewed
   hash and actual confirmation text/source. This operation starts no agent.
3. `feature-planning`, then `feature-plan-tasks`, then `feature-setup`, then
   `feature-delivery`: each uses `New-LiveAcceptanceAuthorization.ps1` and
   `Test-LiveRepositorySync.ps1`, bound to the preceding checkpoint.

These phases together test the complete first vertical slice. A setup checkpoint
or an agent's completion summary is not functional acceptance. After delivery,
run `tests/verify_lending_consumer.py` against its sealed run manifest, the actual
host DLL and the independently provisioned browser modules. This executes real
HTTP/restart, browser/accessibility and current delivery-obligation checks. Local
browser engines are Chromium and WebKit; Firefox remains a CI authority.

## Evidence and learning

Preserve all failures and recovery attempts. `learning_report.py` uses an explicit
inventory of automated run manifests plus `intakeSessions`, `expectedIntakeIds`
and the reconstructed `learning_metrics.intake_usage(...)` records for every human
intake attempt. This binds the preserved TUI rollouts and counts cumulative usage
once per session. Unreported tail usage remains unknown, not zero. Cache is a
subset of input and is reported separately.

Review tokens alongside independent quality and attributable work episodes:
productive work, necessary investigation, avoidable trial/error, unnecessary
reading, external waits and unknown time. Human intake time includes setup and
deliberation; automated process time has a separate stated coverage. Do not claim
numerical savings against the unrelated historical pricing consumer.

The separately prepared v0.11 released reference is for the later upgrade trial.
Its explicit admission is not a historical bootstrap/feature checkpoint. An
upgrade awaiting real governance review remains incomplete until the reviewed
handoff and separately authorized continuation pass independent acceptance.
