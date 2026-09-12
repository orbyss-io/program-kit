# Cumulative release migration guidance for agents

**Status: Deferred — input for a future official intake.** Tracked as
[PK-ARCH-003 in the architecture backlog](architecture-backlog.md#pk-arch-003-cumulative-release-migration-guidance-for-agents).
Saved on 2026-09-12 at the user's request. This is an initial proposal, not an accepted design or
scheduled implementation plan. Begin official intake only when the user chooses this item; revisit
the findings and resolve the scope and decisions then.

## User intent and desired outcome

Every published Program Kit version should supply migration notes for agents upgrading existing
installations. An agent should be able to walk the history between its installed and desired
versions, understand what changed, and determine how to bridge the gap without relying on a
maintainer's conversation or an undocumented recovery handoff.

The proposed distinction is to account for every intervening release while installing intermediate
versions only when necessary. For example, an upgrade from 0.9.8 to 0.10.1 should consider all
applicable changes in that interval and produce one ordered plan. It should avoid repeating
superseded operations or assuming that every patch must be installed in sequence.

Supporting any previous version is the user aspiration. A supported source-version range and
evidence for particular transitions must be established before presenting that as a guarantee.

## Findings at proposal time

These findings describe the inspected 0.10.1 source and release. They are historical observations
to revalidate during intake, not assumptions about the version current when work begins.

| Existing mechanism | What it provides | Remaining gap |
| --- | --- | --- |
| `CHANGELOG.md` | Changes organized by version | Generally lacks applicability checks, ordered consumer actions, and completion criteria |
| README upgrade instructions and `scripts/upgrade_program_kit.py` | Release-owned offline updater, sequential component mutations, version-coherence checks, managed baseline synchronization, and governed upgrade authority | No cumulative release migration index or general read-only planner across a version gap |
| .NET migration catalog and synchronization | Versioned, authenticated file and configuration migrations with applied migration IDs | Covers specific managed changes rather than the full product migration history |
| OpenAPI reconciliation and lock-renewal diagnostics | Explicit producer-pin reconciliation, stale-analysis invalidation, and package-lock renewal instructions | Specialized cases do not establish readiness for every consumer state |
| `docs/releasing-<version>.md` | Maintainer publication and validation procedure | Not a comprehensive consumer migration guide |
| 0.10.1 architecture recovery guide | Evidence-preserving recovery for the reported failed architecture run | Separate discovery and a concrete incident context rather than general migration applicability |

The inspected full `program-kit-0.10.1.zip` did not contain the changelog or the architecture
recovery guide. Its packaged migration guidance included the .NET migration catalog. The published
GitHub release body, as inspected on 2026-09-12, mentioned the earlier PowerShell-diagnostic PR and
omitted the 0.10.1 architecture changes. The follow-up sent to the PriceCalculator task supplied
recovery information that the normal release channel should make discoverable. Correcting the
release body is a future action to consider; this proposal does not perform that correction.

The public upgrade validator selects the immediately preceding stable release and exercises the
older remote workflow/bundle update sequence. The supported local updater has separate regression
coverage, including seeded older version metadata and interrupted mutation recovery. Together,
these checks do not prove arbitrary historical upgrades or readiness of representative existing
approved projects and interrupted workflows.

The updater's word "sequential" refers to component operations within an upgrade. It does not
currently mean traversal of an ordered history of release migration notes.

## Proposed direction for intake

1. **Require a migration entry for every release.** Record affected source versions and project
   states, changed behavior, prerequisites, automatic operations, agent actions, validation, and
   recovery. Explicitly state when no consumer action is required. Distinguish new-install behavior
   from changes needed in an existing consumer.
2. **Ship cumulative guidance and an index.** Include the index and referenced guides in verified
   release archives, make them discoverable from installed agent guidance, and publish the same
   release-specific summary on GitHub. Bind references to the release tag rather than mutable main.
   Offline upgrades should have the migration information they need in the verified release inputs.
3. **Extend the existing updater with read-only planning.** Inspect installed component versions,
   relevant schemas, managed profiles, and workflow state. Select applicable changes across the
   gap and order them into a plan that identifies automatic work, semantic decisions, superseded
   steps, and any required intermediate release. Commands and schemas remain to be designed.
4. **Distinguish installation from migration completion.** Consistent component versions do not
   establish that architecture, feature evidence, or paused workflows are ready. Record migrations
   applied, already satisfied, inapplicable, blocked, or pending, with supporting validation. Reuse
   existing authority and evidence mechanisms where appropriate instead of creating competing ones.
5. **Make migration guidance a release gate.** Validate the current entry, history/index integrity,
   packaged references, and published summary. Exercise the supported updater using the previous
   stable release and selected older compatibility boundaries, including realistic consumer state.

Preserve user work, approved decisions, and failed-run evidence. A mechanical upgrade must not
silently reinterpret product semantics or grant fresh architecture approval. Applicability and
successful validation should determine required actions; agents should not execute every historical
instruction indiscriminately.

Reconstruct older guidance from tagged source, release artifacts, and available evidence. Label
unverified or unsupported transitions honestly. Distribute reconstructed history in a future
release without replacing previously published immutable assets or claiming that old archives
already contained the new guidance.

## Provisional increments

- Establish the migration-entry convention and consumer guidance for the 0.10.1 behavior, and
  resolve the publication/distribution gaps against the then-current release process.
- Package a cumulative index and add discoverability and release checks.
- Add applicability-based planning to the supported updater, including necessary intermediate
  transitions and superseded operations.
- Add migration evidence and expand compatibility fixtures at agreed support boundaries.

These increments are suggestions for scoping the future intake, not a delivery commitment. No
version bump, release modification, updater change, or new release requirement is enacted here.

## Candidate acceptance scenarios

- An agent several versions behind receives all relevant changes and ordered actions using the
  target release's verified inputs, without needing this conversation or an online maintainer guide.
- A patch requiring no consumer migration explicitly reports that outcome without unnecessary
  modification or intermediate installations.
- A transition requiring an intermediate release explains the prerequisite and verifies each
  required stage; unsupported source states produce a specific diagnostic rather than success.
- A paused architecture workflow receives applicable recovery guidance without rewriting its
  approval or history. Completed, unaffected workflows are not unnecessarily rerun.
- A consumer with modified managed files retains local work or receives an actionable conflict;
  retry after interruption does not duplicate completed migrations or conceal pending work.
- An installed component set can be coherent while semantic migration remains pending, and the
  reported readiness makes that distinction visible.
- A release lacking its migration entry or referenced packaged guidance fails the relevant gate.
  Published notes describe the actual release even when tag and merge ancestry differ.
- A reconstructed historical guide states its evidence and limitations; compatibility claims are
  bounded by the agreed and tested support policy.

## Questions to resolve during official intake

- Which historical releases and consumer states must be supported initially, and what constitutes
  enough evidence to extend that support?
- What minimal machine-readable contract makes applicability, ordering, and supersession reliable
  without creating a second workflow engine?
- Where should agents discover guidance before upgrading, and how should refreshed installed
  instructions and paused workflows consume the result afterward?
- How should planning and execution handle mixed-version or partially upgraded installations?
- Which actions can run mechanically under an authorized upgrade, and which changes require
  semantic review under existing governance?
- What evidence establishes completion, where does it live, and how is stale evidence invalidated?
- Which recovery operations are reversible, and when is forward recovery required instead of rollback?
- How should cumulative history be retained as release count grows, including corrections to prior
  guidance and changes to independently versioned runtime components?
- Which real historical fixtures and selected version gaps belong in bounded development tests
  versus the complete publication gate?

## Source anchors for revalidation

The initial analysis used Program Kit v0.10.1, commit
`e39abbdcaf25b90fb78865dc0657fbbf9fce5f01`:

- [Change history](../CHANGELOG.md) and [documented upgrade procedure](../README.md#upgrade-an-existing-program-kit-installation).
- [Supported updater](../scripts/upgrade_program_kit.py) and [OpenAPI reconciliation](../scripts/openapi_upgrade_reconciliation.py).
- [.NET migrations](../extensions/program-kit-dotnet/templates/dotnet/migrations.json) and [managed synchronization](../extensions/program-kit-dotnet/scripts/dotnet_sync.py).
- [Governed version authority](../extensions/program-kit-governance/scripts/governance_state.py).
- [Packaging inputs](../scripts/build_release.py) and [Release workflow](../.github/workflows/release.yml).
- [Local updater regression coverage](../tests/validate_local_upgrade.py) and [public upgrade coverage](../tests/validate_public_upgrade.py).
- [0.10.1 maintainer release guide](releasing-0.10.1.md) and [architecture recovery guide](greenfield-architecture-recovery.md).
- [Published v0.10.1 release](https://github.com/orbyss-io/program-kit/releases/tag/v0.10.1).

Relative source links resolve in the checkout being read; use the recorded tag/commit when
reproducing historical findings. The GitHub release body is mutable, so the observation above is
explicitly dated.
