# Validation Quickstart: Program Kit Adapter for Spec Kit

This guide has two distinct roles:

1. a maintainer prepares one exact unpublished candidate from the clean Program
   Kit repository after protected CI is green; and
2. a reviewer performs each actual journey in one of three empty consumer
   workspaces outside that repository.

The CLI and adapter are not published to NuGet or a public Spec Kit catalog.
The preparation command below builds the exact local packages, catalog, and
dependency mirror used by the review. The automated two-scenario proof remains
`eng/Invoke-SpecKitAdapterQuickstart.ps1`; it does not replace human handoff,
missing-input, authority, or ownership review.

## 1. Exact prerequisites

- PowerShell 7 on Windows or Linux.
- .NET SDK `10.0.302`.
- Spec Kit exactly `0.15.1`.
- A clean Program Kit candidate whose protected CI run is green.
- One new review-root path outside the Program Kit repository.

`specify` is the Spec Kit terminal executable. Verify it before preparing the
seed:

```powershell
specify --version
```

If PowerShell cannot find it after an exact `uv` tool installation, add the
`uv` tool directory to this terminal and retry:

```powershell
$uvBin = (uv tool dir --bin)
$env:Path = "$uvBin$([IO.Path]::PathSeparator)$env:Path"
specify --version
```

Do not run a human journey in the Program Kit repository. Do not copy its
manifest, lock, selection, registration, handoff, factory request, grant, or
product files into a consumer workspace.

## 2. Prepare the candidate, then enter one empty consumer workspace

Run this once from the clean Program Kit repository. `ReviewRoot` must not
already exist:

```powershell
$reviewRoot = 'C:\tmp\program-kit-feature003-review'
./eng/Initialize-SpecKitAdapterHumanReview.ps1 -ReviewRoot $reviewRoot
```

The final JSON must report `"status":"ready"`. The command creates:

- one exact local NuGet feed containing the unpublished CLI and its package
  closure;
- one exact local Spec Kit extension catalog and adapter archive;
- one exact dependency mirror and pinned `global.json`; and
- three genuinely empty directories: `consumer-01`, `consumer-02`, and
  `consumer-03`.

It does not initialize Spec Kit or Program Kit inside those three directories.

In a second PowerShell terminal, from the Program Kit repository, start the
prepared local catalog and leave that terminal open during all three journeys:

```powershell
$reviewRoot = 'C:\tmp\program-kit-feature003-review'
./eng/Start-SpecKitAdapterHumanReviewCatalog.ps1 -ReviewRoot $reviewRoot
```

For the first journey, switch to the first untouched consumer and verify that it
is empty before initializing anything:

```powershell
$reviewRoot = 'C:\tmp\program-kit-feature003-review'
$consumerRoot = Join-Path $reviewRoot 'consumer-01'
if (@(Get-ChildItem -LiteralPath $consumerRoot -Force).Count -ne 0) {
    throw 'This consumer workspace is not empty. Use the next untouched review workspace.'
}
Set-Location $consumerRoot
specify init --here --integration codex
Copy-Item -LiteralPath (Join-Path $reviewRoot 'global.json') -Destination 'global.json'
Copy-Item -LiteralPath (Join-Path $reviewRoot 'extension-catalogs.yml') -Destination '.specify/extension-catalogs.yml'
Copy-Item -LiteralPath (Join-Path $reviewRoot 'dependency-mirror') -Destination 'dependencies' -Recurse
dotnet new tool-manifest
dotnet tool install Orbyss.ProgramKit.Cli --version 1.0.0-alpha.2 --configfile (Join-Path $reviewRoot 'NuGet.Config')
dotnet tool run program-kit -- version --format json
```

Expected:

- Spec Kit created the workspace integration; the review seed did not preinstall
  it;
- the version result identifies `Orbyss.ProgramKit.Cli@1.0.0-alpha.2`;
- the workspace-local tool manifest, not any global Program Kit executable,
  controls CLI resolution;
- no Program Kit profile is selected and no Program Kit factory state exists;
  and
- acquisition used only the prepared local CLI feed and local dependency mirror.

Repeat this section later with `consumer-02` and `consumer-03`. Never copy state
from a completed journey into the next one.

## 3. Neutral Program Kit initialization

In the consumer-rooted task, have the reviewer or authorized agent prepare
one consumer-owned request conforming to
`program-kit.workspace-init-request/v1`. Review the file, then either may run:

```powershell
dotnet tool run program-kit -- init `
  --workspace <consumer-root> `
  --request <consumer-root>/requests/init.json `
  --format json
```

Expected:

- `program-kit.yaml` exists with zero provider/profile selections;
- the result records the bounded bootstrap effect and explicit invocation;
- no catalog refresh, restore, network, provider activation, adapter install,
  factory invocation, or authority occurs;
- repeating the exact command reports unchanged bytes;
- conflicting or unsafe pre-existing paths produce no partial trusted state.

## 4. Create the base lock and inspect local catalog

Use `program-kit.workspace-restore-request/v1` with `mode: base`:

```powershell
dotnet tool run program-kit -- restore `
  --workspace <consumer-root> `
  --request <consumer-root>/requests/restore-base.json `
  --format json

dotnet tool run program-kit -- catalog list `
  --workspace <consumer-root> `
  --request <consumer-root>/requests/catalog.json `
  --format json
```

Expected:

- `program-kit.lock.json` contains the exact distribution/contracts/catalogs
  and an empty selection set;
- the catalog lists the first-party .NET provider and exact
  `dotnet10-cshells-0.0.28@1.0.0` profile;
- the profile is available, not selected, activated, or authorized;
- catalog execution has zero writes and zero network attempts.

## 5. Install the Spec Kit extension and run base doctor

```powershell
specify extension add orbyss-program-kit-adapter
```

The supported project configuration is instantiated at
`.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`
from the adjacent extension-owned template. Commit the project configuration;
do not use the `.local.yml` or environment layers for adapter semantics.

Invoke the registered `speckit.orbyss-program-kit-adapter.doctor` command through
the active AI integration for base scope.

The installation command above is a PowerShell command. Adapter operations are
AI-integration commands. For Codex, open a new task whose workspace is this
consumer directory after installation, then type:

```text
$speckit-orbyss-program-kit-adapter-doctor
```

That is a chat skill, not a PowerShell command. If the short skill name is not
listed in the already-open task, start a new task after installation so Codex
discovers the consumer's installed skills; changing `PATH` will not fix a chat
skill.

Expected:

- Spec Kit registers extension `0.1.0` and its commands/hooks;
- Spec Kit managed core files are unchanged;
- the exact project configuration is consumer-owned and contains activation
  policy but no second profile default;
- base doctor accepts the exact Program Kit release and zero-profile base lock;
- installed, available, selected, activated, and authorized remain visibly
  distinct;
- extension install alone grants no Program Kit effect.

## 6. Prove documentation-only behavior before profile selection

Create a normal Spec Kit feature whose approved scope changes documentation only
and requests no factory output. Run specify/plan/tasks and allow registered
hooks to dispatch.

Expected:

- feature applicability resolves disabled or not-applicable;
- Program Kit child-process invocation count is exactly zero;
- `specs/<feature>/program-kit/` does not exist;
- no profile or authority is requested;
- implementation is not blocked.

## 7. Select the exact factory profile

The consumer or its authorized agent edits the consumer-owned
`program-kit.yaml` to add one named exact selection for the cataloged first-party
.NET provider/profile and optionally names it as the workspace default. Program
Kit does not edit the existing consumer-owned manifest. This manifest/lock is
the only workspace profile-default authority; adapter project configuration
does not duplicate it.

Run a `mode: factory` restore request:

```powershell
dotnet tool run program-kit -- restore `
  --workspace <consumer-root> `
  --request <consumer-root>/requests/restore-factory.json `
  --format json
```

Expected:

- the new lock binds the exact manifest, provider, profile, schemas, contracts,
  dependencies, catalogs, support, and conformance evidence;
- a range, implicit sole choice, stale catalog, or unsupported identity fails
  with no trusted factory lock;
- selecting/restoring grants no construction authority.

## 8. Create and review a factory feature handoff

Run the normal Spec Kit specify/clarify/plan/tasks flow for the Reference Status
example. The adapter does not infer the semantic definition from arbitrary
prose; a human or agent proposes the structured mapping and the named reviewer
owns its approval. Invoke:

1. `speckit.orbyss-program-kit-adapter.activate` for the exact feature;
2. `speckit.orbyss-program-kit-adapter.handoff` to create an absent candidate;
3. human review of applicability, exact inherited/explicit profile, provider
   fields, generated/custom ownership, unresolved/unsupported/deferred/excluded
   meaning, effect ceiling, and field-level trace; and
4. creation of `handoff-review.json` binding that exact handoff and named human.

Then invoke `speckit.orbyss-program-kit-adapter.validate`.

Expected:

- every output-affecting field has one stable source binding;
- custom implementation is explicitly consumer-owned/custom-bounded;
- no authority grant exists in the handoff or review;
- an edit to the handoff stales review;
- an unrelated planning prose edit does not stale traced values;
- a changed named requirement/decision/task block stales only dependent fields.

## 9. Translate, prepare, and explain

After custom implementation referenced by the handoff exists, invoke:

```text
speckit.orbyss-program-kit-adapter.prepare
speckit.orbyss-program-kit-adapter.explain
```

Expected generated closure:

- one provider-specific .NET component/API definition;
- one software-definition bundle;
- exact consumer-owned implementation references;
- exact selection and trace;
- preparation and explain requests/results; and
- an adapter manifest binding inputs, outputs, ownership, and invalidation sets.

`prepare` returns an exact ungranted proposal with request binding, closure,
live state, explanation, blockers, and authority requirements. Neither command
publishes a Program Kit candidate/product or creates/selects a grant.

Repeat translation five times with meaning-preserving input permutations. All
adapter-owned definition/request bytes must match.

## 10. Record human authority separately

After the human reviews the prepared artifact plan, create a separate decision
record conforming to `program-kit.authority-decision-record/v1`. Invoke Program
Kit directly—not an adapter command:

```powershell
dotnet tool run program-kit -- authority record `
  --workspace <consumer-root> `
  --request <consumer-root>/requests/authority-record.json `
  --format json
```

Expected:

- the configured repository authority provider validates exact proposal and
  decision bindings;
- one finite exact grant/revocation pair is atomically recorded;
- no subject, operation, effect, condition, provenance, validity, or identity is
  invented or broadened;
- missing, denied, stale, mismatched, ambiguous, or widened decisions create no
  partial authority file.

This production authority path must be used by at least one package-only
acceptance journey and every human validation journey. A test authority, where
used elsewhere, is separately identified and disclosed.

## 11. Construct and evaluate explicitly

Supply the exact grant reference to `speckit.orbyss-program-kit-adapter.construct`, then invoke
`speckit.orbyss-program-kit-adapter.evaluate`.

Expected:

- the adapter creates the existing valid v1 construct request only after fresh
  preparation/explanation, artifact review, explicit grant supply, and live
  preflight;
- Program Kit performs only the authorized requested effect;
- the adapter result embeds the exact unmodified Program Kit result;
- product, receipt, snapshot, evidence, and captured adapter result are present;
- each generated consumer product builds, passes its tests, starts, and performs
  its demonstrated behavior without Program Kit, Spec Kit, adapter, AI-provider,
  prompt, transcript, or authoring-config runtime dependency.

Repeat with absent, multiple, stale, revoked, widened, wrong-subject, and
wrong-effect grants. Every attempt must produce zero construction.

## 12. Prove the distinct example and mixed workspace

Repeat sections 8–11 for a different component/API with different component,
package, namespace, contract, route, and custom behavior. This journey must not
reuse Reference Status semantic definitions or requests.

In the same workspace, retain an unrelated documentation-only feature. Expected:

- factory feature inherits the exact workspace default visibly;
- documentation feature remains inactive with zero Program Kit invocation;
- changing the workspace default affects new candidates but rebinds zero
  reviewed handoffs.

## 13. Lifecycle and upgrade validation

On Windows and Linux:

1. disable and re-enable the feature;
2. disable and re-enable the extension;
3. update from the previous compatible adapter fixture;
4. attempt an incompatible/interrupted update;
5. perform a manifest-aware compatible Spec Kit upgrade without force;
6. remove the extension with
   `specify extension remove orbyss-program-kit-adapter --keep-config`; and
7. run explicit cleanup against exact and drifted adapter candidates.

Expected:

- consumer config/source/handoffs/reviews and all Program Kit manifest/lock/
  products/receipts/snapshots/evidence remain;
- prior working extension remains selectable after failed update;
- re-enable revalidates rather than silently resuming;
- removal deletes only unchanged extension installation files/registration;
- the exact consumer-owned adapter project configuration remains in place;
- cleanup removes only unchanged proven adapter-generated candidates.

## 14. Verification commands during implementation

Use the cheapest tier that proves the changed boundary:

```powershell
./eng/Invoke-Verification.ps1 -Mode Edit -TestFilter '<affected-unit-filter>'
./eng/Invoke-Verification.ps1 -Mode Story -TestFilter '<story-filter>' -IncludeAcceptance
```

Run once when the local candidate is complete:

```powershell
./eng/Invoke-Verification.ps1 -Mode PrePr
```

Do not routinely run the full acceptance/conformance/cross-platform matrix
locally. Protected CI owns the authoritative merge-candidate proof. After CI is
green, run three fresh human journeys using shipped instructions only.

### The three named human journeys

Each journey starts from the corresponding untouched directory and repeats
section 2. After base doctor succeeds, give the consumer-rooted Codex task only
the matching intent:

| Workspace | Journey | Initial intent |
|---|---|---|
| `consumer-01` | Reference Status | Build a .NET Reference Status API whose `GET /status` endpoint delegates to `Reference.Status.IStatusReader`. Use the Program Kit adapter and stop whenever meaning or authority is missing. |
| `consumer-02` | Inventory Health | Build a distinct .NET Inventory Health API whose `GET /inventory/health` endpoint delegates to `Warehouse.Inventory.IInventoryProbe` and reports degraded state plus backlog count. Use the workspace default and stop whenever meaning or authority is missing. |
| `consumer-03` | Mixed applicability | First complete a documentation-only feature with Program Kit explicitly not applicable. Then build a factory feature with an explicit feature selection override, while preserving the documentation-only feature and stopping whenever meaning or authority is missing. |

The agent may create schema-valid request files and invoke the shown terminal
commands under the reviewer's ordinary workspace authorization. The reviewer
does not need to transcribe JSON or manually run every command. The human work
is to inspect and decide:

1. answer a typed missing-input request in chat instead of letting the agent
   guess;
2. review the handoff and prepared artifact set;
3. explicitly approve or deny the exact construction proposal in chat; and
4. let the agent invoke `authority record` only after that semantic decision.

A chat statement such as “I approve this exact construction proposal” is the
human decision; it is not itself a grant file. Program Kit's repository
authority provider records the bounded grant when the agent invokes the public
command. Hooks and the adapter never do that automatically.

Current limitations are deliberate: the adapter supports one exact Spec Kit
release, one Program Kit release, one compiled .NET profile, and one
component/API definition family. It does not plan work, infer arbitrary
Markdown, create authority, perform migration, dynamically load providers, or
make consumer-authored implementation deterministic.

For each journey, retain one named review proving that the reviewer can:

- locate the tool declaration, manifest, lock, adapter registration, handoff,
  generated inputs, product files, and evidence;
- distinguish installation, availability, selection, activation, authority,
  custom/generated ownership, workspace defaults, feature overrides, and
  non-factory behavior;
- act on both missing-input and authority requests without terminal coaching;
  and
- identify whether Spec Kit, the adapter, Program Kit, the provider, or the
  consumer owns each decision and artifact involved in the journey.

## 15. Required retained evidence

- exact CLI and extension package identities/provenance;
- public schema/catalog/compatibility identities;
- two clean consumer scenario results;
- complete negative/adversarial result matrix;
- repeatability/permutation evidence;
- Windows/Linux install/lifecycle results;
- production authority-recording acceptance;
- consumer runtime dependency inspection;
- claim invalidation/reuse manifest; and
- three named human review records plus final human acceptance.

See [public-cli.md](contracts/public-cli.md),
[adapter-extension.md](contracts/adapter-extension.md),
[schemas-and-artifacts.md](contracts/schemas-and-artifacts.md), and
[diagnostics.md](contracts/diagnostics.md) for the exact boundaries this guide
validates.
