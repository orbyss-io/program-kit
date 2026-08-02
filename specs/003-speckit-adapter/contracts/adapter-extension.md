# Spec Kit Adapter Extension Contract

## Release package

| Property | Exact V1 value |
|---|---|
| Extension ID | `orbyss-program-kit-adapter` |
| Extension version | `0.1.0` |
| Spec Kit requirement | `==0.15.1` |
| Program Kit requirement | `Orbyss.ProgramKit.Cli@1.0.0-alpha.2` |
| Adapter runtime | Framework-dependent `net10.0` executable |
| Supported OS | Windows and Linux |
| Installation | `specify extension add orbyss-program-kit-adapter` |

The package contains `extension.yml`, command instructions, hooks, project
config template `orbyss-program-kit-adapter-config.template.yml`, adapter
executable/dependency closure, schemas, compatibility manifest, diagnostic
catalog, README, license, and release manifest. The release manifest binds all
bytes as one tested set. The instantiated consumer-owned project configuration
is exactly `.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml`.

Installation through Spec Kit proves only **installed**. Base doctor proves
**available/compatible** against the exact workspace-local Program Kit binding.

## Command identities

| Spec Kit command | Maximum effect | Required behavior |
|---|---:|---|
| `speckit.orbyss-program-kit-adapter.doctor` | none | Base or feature readiness and exact compatibility |
| `speckit.orbyss-program-kit-adapter.activate` | config/handoff proposal | Propose explicit feature applicability/profile override; never authority |
| `speckit.orbyss-program-kit-adapter.disable` | config/handoff proposal | Record/propose exact disable; preserve all prior work |
| `speckit.orbyss-program-kit-adapter.handoff` | seeded/adapter files | Propose an absent handoff and show unresolved meaning |
| `speckit.orbyss-program-kit-adapter.validate` | none | Validate config, handoff, review, trace, ownership, paths, staleness |
| `speckit.orbyss-program-kit-adapter.prepare` | adapter files | Translate exact inputs and invoke public `prepare` |
| `speckit.orbyss-program-kit-adapter.explain` | adapter files | Invoke public `explain`; capture exact result |
| `speckit.orbyss-program-kit-adapter.construct` | bounded Program Kit effect | Require exact caller-supplied grant; invoke public `construct` |
| `speckit.orbyss-program-kit-adapter.evaluate` | adapter files | Invoke public `evaluate`; capture exact result |
| `speckit.orbyss-program-kit-adapter.cleanup` | adapter candidates only | Digest-checked removal of unchanged regenerable candidates |

Command instructions are AI-facing guidance. The deterministic executable owns
schema validation, translation, path safety, Program Kit invocation, and result
projection. An AI may propose/edit consumer-owned material only under the
user's ordinary workspace authority; the executable never silently adopts it.

## Executable grammar

```text
dotnet <extension-root>/tools/program-kit-spec-kit-adapter.dll \
  <operation> \
  --workspace <path> \
  --request <path> \
  --format json
```

Operations are the ten command suffixes above. The request is a regular file
inside the workspace conforming to
`program-kit.spec-kit-adapter-request/v1`. JSON stdout is exactly one
`program-kit.spec-kit-adapter-result/v1` document.

The executable resolves Program Kit only from the exact configured .NET local
tool manifest and invokes:

```text
dotnet tool run program-kit -- <public-command-arguments>
```

It uses an argument vector, shell execution disabled, bounded stdout/stderr,
explicit working directory, empty semantic environment inputs, and a bounded
timeout/cancellation policy. It validates stdout before retaining it and never
copies raw stderr into ordinary results.

## Hook contract

| Hook | Command | Behavior | Blocking rule |
|---|---|---|---|
| `after_plan` | `handoff` | Resolve applicability; optionally propose handoff | Only unresolved `required` may block its gate |
| `after_tasks` | `validate` | Check ownership/task obligations for applicable feature | Only explicit/required applicable work |
| `before_implement` | `validate` | Require current reviewed handoff and complete meaning | Never for inherited unactivated `assist` |
| `after_implement` | `prepare` | Refresh implementation bindings and offer effect-free preparation | Never constructs; never acts for inactive feature |

Every hook first resolves feature override, project mode, and applicability.
For disabled/not-applicable work it returns `not-applicable` with zero Program
Kit process launches, zero profile resolution, zero feature artifacts, and no
workflow blockage.

Hooks never invoke Program Kit `init`, `authority record`, or `construct`, and
never select a grant.

## Activation/default resolution

Activation mode resolves as:

```text
feature mode override -> repository project defaultMode -> off
```

Applicability resolves before profile. Only an applicable feature may resolve
an exact feature selection override or `defaultSelection` from the current
Program Kit workspace lock. Adapter project config defines no second profile
default. A reviewed handoff pins the effective mode/selection and whether each
was explicit or inherited. Later default changes report divergence; they do not
regenerate or rebind the reviewed handoff.

Local config, environment variables, path globs, installation order, and the
mere presence of one profile are never semantic inputs.

## Lifecycle contract

- **Update** replaces only extension-owned installation files after complete
  validation; incompatible/interrupted update retains the prior selectable
  release.
- **Spec Kit upgrade** uses the manifest-aware supported path, preserves
  registration/project layers, and requires no force option.
- **Disable** removes commands/hooks from active use and changes no consumer or
  Program Kit artifact.
- **Re-enable** revalidates preserved state and never resumes an old effect
  continuation silently.
- **Remove** uses
  `specify extension remove orbyss-program-kit-adapter --keep-config` and deletes
  only unchanged extension installation files and registration. The exact
  consumer project config, handoffs, generated evidence, Program Kit
  state/product, and consumer work remain.
- **Cleanup** is separate and governed by the artifact contract.

## Consumer-only boundary

The Program Kit repository never installs or executes this adapter to build
itself. Build-time unit/contract tests may reference the adapter project, but
every behavioral installation/factory claim is proven from a separately staged
package in a temporary consumer workspace.
