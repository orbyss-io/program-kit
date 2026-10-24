# Program Kit internal modularity design

Date: 2026-10-24. Status: approved by the user; implemented locally; see the [implementation review](modularity-implementation-2026-10-24.md) for validation and limits.

Checkout: `codex/bootstrap-intake-analysis`, source `4a3455ca2366121e8bc1cab4ad9e4f4cdbbb57f5`. Preserve the branch's intake/epic improvements. The main checkout's unrelated work is outside this change.

This is the current design. It narrows the earlier [distribution/knowledge investigation and grilling record](distribution-and-knowledge-review-2026-10-23.md). The future pack ecosystem is recorded in [GitHub issue #57](https://github.com/orbyss-io/program-kit/issues/57) and is out of this implementation scope.

## Outcome and boundaries

Program Kit remains the product and owns its coherent user experience. Spec Kit supplies the existing consumer feature lifecycle and native integration mechanisms. Keep a clear Program Kit front door and native phase vocabulary where it already expresses the work well.

The current work makes the implementation easier to maintain, distributes appropriate built-in content and delivers relevant knowledge in smaller decision contexts. Priorities are dependable knowledge, simpler maintenance and appropriate consumer content; robust packaging is required throughout. Extra files are acceptable where eliminating them would require disproportionate machinery.

**Build now:** internal responsibility/dependency boundaries; a clean distinction between integration and payload distribution; existing capability/profile-based applicability; knowledge/prose consolidation; focused context delivery; supported migration and preservation.

**Defer to #57:** public pack contracts/loaders, a Pack SDK or authoring wizard, a new general configuration wizard, local/private installable pack authoring, pack registries/index admission and publisher workflows, arbitrary third-party executable plugins, pack dependency/version/conflict management and external-host integrations. No new Node/Python/Semantic Kernel engineering support is promised. Existing local coding-pattern behavior remains supported.

The future requirement is an architectural constraint: current capabilities should have understandable owners, inputs, dependencies and outputs so they can later become pack contributions. Do not freeze a speculative public ABI or implement a miniature pack manager as part of modularity.

## Internal responsibility boundaries

| Area | Owns | Boundary |
| --- | --- | --- |
| Native Spec Kit integration | Command/skill rendering, phase hooks, preset additions/replacements and bootstrap workflow gates | Calls the actual implementation owners. It is not the default container for every example, capture and maintenance input. Preserve native IDs and supported invocation behavior during migration. |
| Stack-neutral Program Kit runtime | Common lifecycle/context/schema/source-reading and verification plumbing that does not depend on a selected engineering stack | Move genuinely common helpers out of .NET-owned source dependencies. Keep .NET rules/generators with their actual owner; avoid relabeling all existing engineering code as common. |
| Engineering/capability implementations | .NET/building-block/UI-specific selection, generation, synchronization and executable checks | Operate on accepted capability/profile and actual project/component scope. Declare required dependencies; no global backend assumption solely because toolkit files exist. |
| Canonical knowledge | Authored rules, exact source selectors, applicability, guidance routes and useful specialized examples | Reuse `phase-obligations.json` and its existing discovery/context owners. One canonical authority; derived views do not become a competing rule source. |
| Assets and retained history | Native engineering templates, optional UI/examples, exact publisher captures, qualified profiles, migration/source-recovery data | Distinguish active runtime inputs, selected references, optional assets, maintainer-only work and historical compatibility. Preserve required originals and exact identities. |

These are source/ownership responsibilities, not five new packages or installable extensions. Choose concrete folders/imports through the existing producers and callers during implementation. Preserve provenance and consumer customizations when managed/generated copies are emitted.

Application-owned `eng/`, build files, locks and contracts remain real executable consumer inputs. Application compilation/deployment must remain independent of Spec Kit, agent skills and the Program Kit authoring installation.

## Applicability and dependencies

Use the existing accepted intake/decision register, building-block selection, qualified profile context, native project ownership and task paths to select current capabilities. Reuse existing capability and rule registries; do not introduce a second authoritative module inventory.

Keep three facts separate:

1. Toolkit bytes are installed or available.
2. The project/component has adopted a capability or provider.
3. The current phase/task/decision needs its guidance or execution.

No newly invented pack enable/disable system is needed for this separation. Installed .NET source is not proof that a frontend task owns backend duties; a mention of forms is not itself adoption of Orbyss Forms. Preserve explicit project selections and disclosed applicable defaults.

The dependency audit found selective application materialization already exists. Domain Events resolved offline without Forms/Localization; selected Forms currently requires Localization. Preserve that real dependency rather than removing packages to achieve an arbitrary smaller count.

Whole-profile qualification remains broader than runtime package selection. Clarify those responsibilities and scope operational inputs where the existing contract permits it. Do not omit qualification checks or rewrite original evidence merely because a family is not selected for one application. A supported split of qualification is separate from deleting supposedly unused metadata.

Separate stack-neutral helper imports before attempting to omit a .NET toolkit payload. Today governance imports common helpers through `dotnet_adapter.py`; simply skipping that extension can break generic commands before applicability selection. This is a concrete dependency repair, not a request to deliver fully managed alternative stacks.

Device checks should eventually follow the actual built-in capability/operation prerequisite owner rather than require unrelated toolchains. Reuse the existing read-only diagnostic and human-run remediation policy; no new configuration wizard or device installation by an agent is included.

## Distribution

The initial archive build measured 507 composite entries against a 512-entry limit. A five-file manifest/metadata experiment parsed to the same native bundle definition. Component archives were individually below the limit. Full safe extraction of the composite rejected an 18,193,482-byte historical facts member; normal manifest parsing did not extract that member. These establish distinct packaging contracts to validate.

Proposed packaging change:

- Make the Spec Kit bundle a small composition artifact pointing to the existing native components.
- Give complete updater/tooling/source-recovery contents a separately named, verified distribution artifact from the same package build.
- Update actual initializer, updater, witness/recovery and test consumers together before changing which artifact supplies their inputs. Preserve prior source/recovery recognition and explicit local/offline routes.
- Keep exact package/source identities and checksums. Validate entry count, member/total byte limits and extraction behavior for each real consumer route; avoid further compaction solely to squeeze under one ceiling.
- Reduce default component payloads only after tracing actual runtime, selected reference and historical consumers and proving the replacement route. Retain required qualified profiles, existing consumer locks and native ownership baselines.

This is release distribution using existing mechanisms, not dynamic pack installation. Native component registration remains the supported consumer integration route. No new global runtime, module downloader or package manager is introduced.

## Knowledge and prose

The existing discovery system has 63 source records and 308 rule records at the reviewed source. It distinguishes active, conditional, manual, routing and historical material. Extend its real routes and migration dispositions rather than create another maintained knowledge catalog.

Review each currently shipped family through these dispositions: active core; conditional capability/technology guidance; point-of-use reference/example; maintainer-only; historical compatibility; or retirement after proof. Static filename references are investigation leads, not deletion authority. Account for dynamic schema names, directory readers, selected publisher readers and real independent tests.

Retain useful specialized knowledge. Publisher facts already inform wire contracts, settings/composition and Foundation applicability. Functional discovery and this branch's detailed feature seeds remain important inputs. Examples such as snapshot query, evidence submission and PostgreSQL lifecycle should become easier to find when relevant, rather than vanish because they are optional.

Context reduction is a current requirement independent of packs. A synthetic probe of the current canonical constraint renderer emitted 36,461 bytes for generic tags, 74,343 for TypeScript/browser and 175,549 for a mixed selection. These are illustrative constraint outputs, not measured complete agent contexts or token counts.

The desired delivery is:

- Small capability/source discovery when choosing an approach.
- Applicable canonical clauses before the specific decision or action they govern.
- Examples, diagnostics and exact-version source through focused deeper lookup.
- Fewer duplicated instructions, rationale essays and specialized procedures in ordinary briefs.
- Preserved mandatory conditions, exceptions, governing project decisions and source attribution.

Use the same canonical owners for guidance and evaluation. Do not replace complete rules with an independently maintained lossy summary. Pagination alone does not solve cumulative context growth. Measure the assembled phase/operation context including wrappers, set its aggregate budget in the existing validation owner before changing that route, and expose overflow through narrower work or an explained exception. Exact budgets are an implementation measurement/review task, not a reason to ask the user to guess token counts.

## Implementation sections and proof

| Section | Inspectable result | Meaningful proof |
| --- | --- | --- |
| 1. Trace and establish owners | Producer/caller and installed-output map for the five internal areas; current representative context snapshots; explicit keep/move/retire dispositions | Existing discovery/selector checks, exact source/installed route inspection and independently chosen inclusion/exclusion cases. Use the dated audit as a starting point rather than a new permanent registry. |
| 2. Separate common helpers | Common runtime ownership and stack-specific imports have real boundaries; current native commands retain their behavior | Fresh-process entrypoints, generic and selected-stack cases, missing-adapter diagnostics where appropriate, native generated-output preservation. No unsupported alternate-stack claim. |
| 3. Separate distribution carriers | Small native bundle plus complete explicit tooling/recovery artifact; all supported references point to the correct source | Actual archives and native installation; source recovery, installed command/hook behavior, supported predecessor upgrade, managed-edit refusal and interrupted retry. Use the actual CI Spec Kit pin for qualification. |
| 4. Improve knowledge routes and briefs | Useful material has real applicability routes; ordinary guidance is smaller and less repetitive; canonical duties and focused detail survive | Before/after assembled contexts, relevant/unrelated/unknown-owner cases, source/version resolution and semantic review of changed clauses. Maintain independent expectations instead of deriving tests from the same registry values. |
| 5. Remove proved redundancy and finish migration | Unnecessary default payload/policy duplicates are consolidated through their owners; compatibility/history are retained where needed | Installed/package fidelity, selected asset and historical lookup, preserved locks/authored files and targeted affected regressions. A passing hash check alone is not semantic proof. |

Follow repository Integrity then Affected selection through `tests/validation-inventory.json`. Expensive mechanisms need a concrete affected contract and focused reason. Respect local Firefox and other host limits; relevant CI owns unsupported local platforms. No automatic full inventory/browser matrix, device-tool installation, coding-agent validation, paid/provider activity, publication, tag or commit/push follows from this design.

## Questions and next boundary

No blocking product questions remain for this internal modularity design. The pack-specific conflict, version/update, SDK and admission questions are assigned to #57 and must be reopened when that feature is designed, rather than silently assumed answered here.

Existing consumer preservation, explicit selections, native lifecycle ownership and canonical knowledge remain the defaults for this implementation. Concrete module/file layouts, context budgets and supported asset closures are implementation-owner tasks to resolve through source inspection, measured output and review of each section. An observed compatibility contradiction is brought back with evidence rather than resolved by weakening an existing contract.

The user approved this synthesis and authorized implementation of its sections. See the [implementation review](modularity-implementation-2026-10-24.md) for source ownership, actual outputs, validation and remaining proof limits. A public pack system remains out of scope.
