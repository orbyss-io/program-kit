# Capability consumer integration postures implementation plan

Canonical source: `implementation-plan.json`
(`sha256:2d9bbfe4d45289322fad65c7971dce2618be43197f31ca3b64cf5831d334106e`),
governed by Planning `3.0.0`.

The plan implements only Architecture Design `2.0.0`
`pkid:design:program-kit:capability-consumer-integration-postures@1.0.0`,
`sha256:666cf457a32702cd8ecf29fbdf412a99bd7187e953c5e1696d82bd4d6fa9d1b0`.
If this projection differs from the canonical JSON, the JSON governs.

State: `ready-for-human-decision`. No work unit is authorized until a human
approves the exact canonical design and plan digests together.

## Static-conformance binding

The plan uses the human-selected `reuse-existing` disposition:

- disposition:
  `sha256:aa422e16ebbfc5fb038a29adbfd5d9072122292543f82b07ca9e8c87cbb340af`;
- existing Program Kit private C# gate:
  `pkid:policy:program-kit:csharp-source-quality-gate@1.10.0`,
  `sha256:e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1`;
- activation matrix:
  `sha256:bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b`;
- exhaustive verification profile:
  `sha256:80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d`;
- private selection lock:
  `sha256:1cfb2a26ecf273cacae5062f04c4f42e95eb88e08323998a99a8d6aa6ad4291a`;
- existing activation evidence:
  `sha256:c4b247449959317dd95eca5aab4baf61d709ff27155e84cae0a9d111f0e4b09b`.

There is no gate-establishment work unit. The existing private gate applies
only to Program Kit-owned C# implementation.

## Work units

### `PKCI-W010` — reviewed provider contracts

Establish the finite provider registry and current project-skill roots:
Codex `.agents/skills` and Claude Code `.claude/skills`. Keep
`.codex/skills` only as exact legacy migration input. Recheck official provider
evidence and stop on material contract drift or any need for global, trust,
permission, hook, MCP, runtime, or speculative integration.

### `PKCI-W020` — multi-provider ownership lock

Introduce a deterministic versioned lock containing the complete exact set of
Program Kit-owned provider bindings. Accept the legacy single-provider lock
only for strict migration. Reject duplicates, unknown state, ambiguous
ownership, and path escapes.

Depends on `PKCI-W010`.

### `PKCI-W030` — transactional initialization and migration

Add or update one provider without losing another provider's ownership.
Migrate exact legacy lock and Codex wrapper bytes to current state.
Tamper, collisions, incomplete bundles, cancellation, or invalid recovery state
must not produce partial externally visible ownership.

Depends on `PKCI-W020`.

### `PKCI-W040` — explicit exact removal

Add `capabilities uninitialize` for one explicitly selected provider. Remove
only exact lock-owned bytes, preserve other providers, and remove the lock when
the owned set becomes empty. Never infer or persist consumer posture.

Depends on `PKCI-W030`.

### `PKCI-W050` — canonical capabilities and bundle revision

Use the repository-owned `author-and-maintain-skills` flow to update canonical
provider guidance and thin wrappers. Produce a new exact bundle revision and
align package and delivery conformance. Stop if the active provider wrapper is
missing or canonical guidance would be changed through an improvised route.

Depends on `PKCI-W040`.

### `PKCI-W060` — posture guidance and consumer migration

Document `none`, `local-optional`, and `repository-managed`, including exact
pinned setup/removal commands and selective Git tracking guidance. Program Kit
does not edit `.gitignore` or Git state.

Preserve the Domain Semantic Engine's current `repository-managed` Codex
choice while coherently superseding its pending CapabilityBundle `3.0.0`
initialization with the verified new bundle, current `.agents` wrappers, and
multi-provider lock. Preserve all unrelated consumer and Program Kit worktree
bytes, including unrelated web-publication work.

Depends on `PKCI-W050`.

### `PKCI-W070` — closure

Run the mandatory private-gate build, full unit and conformance suites, exact
bundle packing, initialization and removal fixtures, clean-checkout
repository-managed discovery, runtime dependency-isolation checks,
documentation review, digest checks, and unrelated-byte-preservation proof.

Depends on `PKCI-W060` and transitively closes every product work unit.

## Requirement outcomes

| Requirement | Observable outcome |
| --- | --- |
| `PKCI-R001` | Every consumer owns and states one posture; Program Kit does not infer it. |
| `PKCI-R002` | A fresh contributor sees the selected posture and exact pinned setup/removal documentation. |
| `PKCI-R003` | Only finite, fully reviewed provider adapters initialize. |
| `PKCI-R004` | Codex writes beneath `.agents/skills`; Claude Code writes beneath `.claude/skills`. |
| `PKCI-R005` | Initializing one provider preserves exact ownership of every other provider. |
| `PKCI-R006` | Exact legacy locks and Codex wrappers migrate; ambiguous or modified state remains untouched. |
| `PKCI-R007` | Explicit removal deletes only the selected provider's exact owned bytes. |
| `PKCI-R008` | No `.gitignore`, Git-index, global-provider, trust, permission, runtime, or work-authority mutation occurs. |
| `PKCI-R009` | Deterministic transactions preserve the pre-operation state on refusal, cancellation, or recovery failure. |
| `PKCI-R010` | The new bundle binds every canonical capability and reviewed adapter byte exactly. |
| `PKCI-R011` | A fresh Domain Semantic Engine clone discovers its committed Codex integration at the current path without unrelated changes. |
| `PKCI-R012` | Mandatory gate, tests, bundle, clean-checkout, runtime-isolation, documentation, and preservation evidence all close. |

## Stop boundary

Implementation stops on material provider-contract drift, architectural
deviation, ambiguous ownership, any forbidden global/Git/runtime mutation,
failure of exact migration or removal, inability to preserve existing human
work, or any mandatory closure failure. Publication, release, deployment,
additional providers, hooks, MCP bindings, global installation, and autonomous
behavior remain outside this plan.
