# Validation Quickstart: Program Kit Adapter for Spec Kit

This is the planned package-only validation journey for the completed feature.
It is not an implementation script and is not runnable until the tasks are
implemented. Exact request examples will live in the packaged acceptance
fixtures; this guide references their schemas rather than duplicating them.

## 1. Exact prerequisites

- Windows or Linux clean consumer workspace.
- .NET SDK `10.0.302`, roll-forward disabled.
- Spec Kit exactly `0.15.1`.
- Local/offline package source containing:
  `Orbyss.ProgramKit.Cli.1.0.0-alpha.2.nupkg`.
- Adapter extension archive/catalog entry:
  `orbyss-program-kit-adapter` `0.1.0`.
- Exact dependency mirror required by the generated .NET product.

The Program Kit repository is not the consumer workspace. No Program Kit
manifest, lock, profile selection, adapter registration, handoff, definition,
bundle, factory request, grant, or product file may be copied into the clean
workspace.

## 2. Initialize Spec Kit and acquire Program Kit locally

From the empty consumer workspace:

```powershell
specify init --here --integration codex
dotnet new tool-manifest
dotnet tool install Orbyss.ProgramKit.Cli `
  --version 1.0.0-alpha.2 `
  --add-source <exact-local-feed>
dotnet tool run program-kit -- version --format json
```

Expected:

- the version result identifies `Orbyss.ProgramKit.Cli@1.0.0-alpha.2`;
- acquisition changes only .NET-owned tool-manifest/package state;
- no profile is selected and no Program Kit workspace/factory state exists;
- a global `program-kit` executable, if present, is irrelevant.

## 3. Neutral Program Kit initialization

Create one consumer-authored request conforming to
`program-kit.workspace-init-request/v1`, then run:

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

Invoke the registered `speckit.program-kit.doctor` command through the active
AI integration for base scope.

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
example. Invoke:

1. `speckit.program-kit.activate` for the exact feature;
2. `speckit.program-kit.handoff` to create an absent candidate;
3. human review of applicability, exact inherited/explicit profile, provider
   fields, generated/custom ownership, unresolved/unsupported/deferred/excluded
   meaning, effect ceiling, and field-level trace; and
4. creation of `handoff-review.json` binding that exact handoff and named human.

Then invoke `speckit.program-kit.validate`.

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
speckit.program-kit.prepare
speckit.program-kit.explain
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

Supply the exact grant reference to `speckit.program-kit.construct`, then invoke
`speckit.program-kit.evaluate`.

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
./eng/Invoke-Verification.ps1 -Mode Fast
./eng/Invoke-Verification.ps1 -Mode Contract
```

Run once when the local candidate is complete:

```powershell
./eng/Invoke-Verification.ps1 -Mode PrePr
```

Do not routinely run the full acceptance/conformance/cross-platform matrix
locally. Protected CI owns the authoritative merge-candidate proof. After CI is
green, run three fresh human journeys using shipped instructions only.

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
