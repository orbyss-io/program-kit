# PDF.js retained assets maintenance investigation

The maintenance request has substantial merit, but its upstream scope should be **HostedPages retained-inventory preflight and explicit retirement in Program Kit**. The evidence does not establish a PDF.js defect or an incorrect native HostedPages budget algorithm. Native admission rejects a genuinely over-budget retained inventory. Program Kit's preparation and packaging path can carry that inventory through to activation without detecting the relevant native limits.

The recommended disposition is to accept a focused Program Kit repair, reject the interpretation that PDF.js or BFF needs fixing, and keep shared-asset memory deduplication as a separate optional Foundation improvement. Raising the deployment budget is a supported capacity decision; making every deployment use the maximum is not a retention solution.

This investigation changed no production implementation, consumer source/configuration, dependency pins, vendor bytes or repair ledger. It evaluates the supplied maintenance prompt, not a sealed repair-feedback packet or a registered owner's adoption decision.

**Evidence and version identity.** The scoped consumer is `C:/Users/tech_/pk_trial_claim_2`; the maintenance checkout is `codex/bootstrap-intake-analysis`, based on `88477de14db70837f342f87854d375c4e0ce1f69`, including the preceding uncommitted prevention work. The selected consumer package is HostedPages **0.3.7**, and `web/package.json` selects PDF.js **6.4.299**. The actual HostedPages DLL used by the diagnostic has SHA-256 `867e5c49a328fad4d6eac6c0ede90d080d56f0ad0d724aeb2d1016906b00942b`.

The package nuspec identifies Foundation source commit `b7802042ea3e68a2d4e533b4938674e2d5a4a6c5`. Four relevant files read from that exact commit match the source hashes in the actual package's settings metadata. This avoids treating the Foundation repository's newer checkout as the selected contract. The [package and source identity proof](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/selected-source-proof.json) retains the identities and selected settings.

The consumer's `hosted_bundle.py` and captured manifest producer match the publisher bytes. Its preparation script differs in source-input discovery, but its `build` and `admission` function bodies match the publisher exactly. The retention finding therefore applies to the maintained implementation, rather than only to a consumer customization. See the [function comparison](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/function-comparison.json).

The consumer continued building independently during investigation. Quantitative reproduction uses the frozen eight-revision snapshot identified below; a later observation had nine revisions. The original eight-revision manifest bytes were recovered from their content-addressed history and hash-checked. Findings are not assertions about an indefinitely changing working tree. [Snapshot drift evidence](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/consumer-drift.json).

**What the retained inventory actually costs.** The request's seven-revision observation is supported by retained history: **38,313,788 descriptor bytes**. In the captured eight-revision source and staged bundle, the corresponding count is **44,577,423 bytes**, despite only **11,035,314 unique physical asset bytes** across fifteen files. The manifest SHA-256 is `bbefaa59e954b323ab7250c3aac4b9df1ec7f4e9705be6892525f18af6803f60`.

The retained chain's six-revision prefix already totals **32,050,167 bytes**, slightly over the default. Seven revisions describe the reported incident; they are not the first mathematically over-budget prefix. The captured current revision alone costs **6,263,635 bytes**, which fits the default. This is cumulative retention pressure, not evidence that one current viewer build exceeds the default.

The frozen inventory reuses a **3,830,450-byte** PDF resource module and a **1,192,494-byte** worker in seven revisions each. Filesystem deduplication is already effective. It does not change the native admission count. [History](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/history-inspection.json), [shared assets](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/shared-assets.json), and [staged configuration inspection](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/staged-inspection.json).

The staged shell explicitly selects `MaxTotalBytes=128000000`. That configuration admits the captured inventory. The authored input and generated staged shell are different views; the effective HostedPages configuration must be inspected after composition, rather than inferred from an arbitrary input file alone.

**The selected native contract differs from the packaging ceilings.** These are byte counts, not interchangeable MB/MiB labels:

| Limit | Actual native HostedPages 0.3.7 | Current Program Kit inventory check |
| --- | ---: | ---: |
| Aggregate asset budget when omitted | 32,000,000 | No effective-default check |
| Maximum configurable aggregate budget | 128,000,000 | Fixed 134,217,728-byte inventory ceiling; setting itself is not checked |
| Retained revision count | 1 through 16 | No revision-count bound |
| Individual asset | 8,000,000, also capped by remaining aggregate budget | 8,388,608 |
| Manifest | 2,000,000 | 2,097,152 |

The per-file and manifest unit differences are adjacent source-confirmed mismatches; they did not cause the reported viewer failure. No asset in the frozen inventory exceeds the native per-file maximum. The selected options source/XML itself misleadingly describes the aggregate cap as “128 MiB”; its executable condition and settings metadata both specify **128,000,000**. That is a small Foundation documentation inconsistency, not evidence that its implementation should accept 134,217,728.

Native admission loops over every revision and every descriptor, reads a separately bounded byte array, and adds its length to one aggregate counter. It stores revision-owned admitted byte snapshots. Repeated descriptors therefore count again even when their file path/hash is shared. This is executable behavior, not an assumption about disk size. The exception mentions an asset because the read is capped by the *remaining aggregate allowance* as well as the per-file maximum. It does not establish an oversized individual file. [Exact selected catalog](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/selected-source/HostedPageCatalog.cs), [asset admission](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/selected-source/HostedAssetAdmission.cs), and [options](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/selected-source/HostedPageOptions.cs).

**Independent reproduction.** A disposable .NET diagnostic loaded the actual cached 0.3.7 assembly and the public local asset source against copied public assets. It invoked the internal admission constructor by reflection solely for diagnosis; it did not rebuild the supplier implementation or introduce a maintained consumer dependency on internals. Eleven cases produced their expected native outcomes:

| Case | Program Kit inventory | Actual native admission |
| --- | --- | --- |
| Frozen eight revisions, omitted budget | Accepts | Rejects at 32,000,000 |
| Same inventory, configured 128,000,000 | Accepts | Accepts |
| Same inventory, exactly 44,577,423 | Accepts | Accepts |
| Same inventory, one byte less than required | Accepts | Rejects |
| Explicitly keep original first and current revisions, 7,041,827 bytes | Accepts | Accepts at the default |
| Sixteen tiny valid revisions | Accepts | Accepts |
| Seventeen tiny valid revisions | Accepts | Rejects revision count |
| Tiny inventory, setting 128,000,000 | Accepts | Accepts |
| Tiny inventory, setting 128,000,001 | Accepts | Rejects settings |
| Tiny inventory, setting 134,217,728 | Accepts | Rejects settings |
| One shared 6,000,000-byte JS file described in six revisions | Accepts | Rejects the default aggregate budget at 36,000,000 descriptor bytes |

The explicit subset also preserves both kept revisions' native snapshot hashes. Removing unrelated revisions does not inherently require changing a kept revision or its asset identity. This is identity/admission proof, not an HTTP proof that old URLs were fetched. Native build completed with zero warnings/errors and all eleven outcomes matched. [Probe source and execution](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/native-probe/Program.cs), [native outcomes](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/native-probe/native-results.json), and [final run](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/native-probe/final-run.log).

A separate mechanism probe exercised the actual preparation wrapper and byte-identical captured producer with controlled fictional Vite outputs. An unchanged build retained the same manifest/revision. Changed builds accumulated seventeen revisions, and freshness admission still succeeded. Explicitly selecting a two-revision subset before a subsequent unchanged build worked without changing the kept revision objects. Thus manual retirement is technically possible, but the ordinary preparation CLI has no declared keep/retire policy. This probe did not run npm, Vite or a browser; the distinction matters when assessing build integration. [Retention mechanism results](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/retention-results.json).

**Disposition by responsibility.**

| Observation or proposed interpretation | Assessment |
| --- | --- |
| Program Kit uses binary generic ceilings and ignores effective native budgets/revision count | Confirmed shared validation gap, with incorrect “supported maximum” ceilings. Accept a focused repair. |
| Every changed build retains all earlier revisions without a maintained retirement selection | Confirmed lifecycle/workflow gap. Accept bounded policy and explicit retirement support; do not invent which old URLs the product may abandon. |
| Native HostedPages should have accepted the reported default-budget deployment | Reject this interpretation. It correctly rejects the inventory under its selected contract. |
| Native duplicate accounting is necessarily a supplier defect | Not established. It matches the selected implementation's revision-owned snapshots. Sharing immutable memory could be a separate optimization proposal. |
| PDF.js 6.4.299 is broken or needs replacing | Not established. The failure occurs in native asset admission before the viewer executes. |
| Raising the budget is inherently an improper workaround | Reject this interpretation. The selected value is supported and the snapshot fits; it does not supply an indefinite retention policy. |
| Stale sealed packs, `--no-build`, bind-mount replacement or login before readiness imply BFF defects | No causal support. Treat these as the separate workflow errors described in the request, not a reason to replace authentication. |
| Native comments use the wrong unit for the aggregate maximum | Confirmed documentation inconsistency; handle separately from runtime behavior. |

There is an important qualification to the Program Kit finding: `hosted_bundle.py` explicitly assigns semantic content admission to Foundation, and preparation's `applicationAcceptance` remains false. Existing composition guidance also separates preparation from native readiness. A successful build/stage was never comprehensive application acceptance. The narrower supported criticism is that cheap, deterministic limits are absent or inconsistent at the deployment boundary, allowing predictable activation failure after the normal preparation path. Full duplication of native media admission would be the wrong remedy.

**Could this have been avoided?** Yes, at both the consumer and toolkit levels. The selected metadata and package documentation expose the default, maximum and sixteen-revision bound. An explicit retained-inventory/capacity decision before deployment would have prevented this incident. A native activation smoke check before promoting a replacement would also have caught it. There is no retained trace here establishing which source the original implementer actually consulted, so availability of that knowledge is not proof it was read or deliberately ignored.

The supported binary-data factory and relative/content-hashed build are valid integration choices under the selected media contract. The installed PDF.js declarations/source expose `BinaryDataFactory` and `useWorkerFetch`; the consumer uses its own bounded lookup with `useWorkerFetch=false`. Its Vite plugin emits an ordinary JS module containing encoded trusted resources. That differs from relabelling raw binary bytes as JavaScript. The larger closure makes the retention problem visible sooner; smaller resources would still eventually hit the revision limit. Optimize bundle contents only against actually required and qualified viewer behavior, not by removing trusted resources until a budget happens to pass.

The retained consumer pack log shows staging success. The inspected Chromium test and result exercise actual login, document controls, canvas/text rendering, zoom, pixel bounds, desktop/phone themes and cleanup after the override. This supports the local remedy for the exercised sample. It does not prove every font/CMap/WASM case, all retained old URLs, Firefox, or general PDF compatibility. Those checks were inspected, not independently rerun against the consumer. [Retained browser result](C:/Users/tech_/pk_trial_claim_2/artifacts/browser/ui-feedback/result.json) and [actual test](C:/Users/tech_/pk_trial_claim_2/tests/web/policy-ui-feedback.spec.mjs).

**Recommended repair boundary.** Keep the change in the existing preparation, inventory/staging and composition guidance owners:

1. Evaluate byte/revision counts against each selected deployment's effective composed HostedPages settings and selected-version bounds. Preserve authored lower/higher overrides and decimal units. Count every admitted descriptor; count unique disk bytes separately for diagnostics. Report counted bytes, configured/default budget, revision count and supported remedies. A frontend shared by several shells needs each selected shell checked, not a silently invented global maximum.
2. Add an explicit retention selection or operator-chosen bounded policy. Preserve current and deliberately supported revisions; refuse an over-budget proposal before promotion if no valid selection is supplied. Do not silently apply an arbitrary “last N” policy, delete consumer files, or change old revision objects. A selected subset can feed the existing unmodified producer. Keep historical release archives separate from the actively served inventory.
3. Preserve native runtime admission as the final authority. The selected catalog is internal; the diagnostic's reflection technique is not a proposed production seam. Reuse a supported native preflight capability if available, or add only the missing budget/count checks using attributable selected contracts. Do not build a second MIME/parser/HostedPages implementation.
4. Maintain point-of-use guidance and upgrade instructions. Preserve the working PDF.js factory/worker integration, BFF, content hashes, locks, authenticated originals and source-backed settings. Never auto-set every deployment to the maximum. Correct misleading MB/MiB wording through the proper owner rather than modifying captured vendor bytes.

Qualification should cover unchanged/changed builds; one shared large resource across revisions; omitted, lower and nondefault overrides; aggregate equality and one-byte overflow; sixteen/seventeen revisions independently of byte pressure; effective settings after composition; and explicit retirement with unchanged kept snapshot hashes. A focused published-host/browser scenario should then fetch kept old URLs, verify deliberate retirement behavior, and load the current pinned worker plus static/dynamic resource closure. Reuse existing fixture owners and native producer; no broad unrelated authentication or full release matrix is implied.

Migration should begin from a counted, preserved last-good manifest and a deliberate set of supported URLs. Author the capacity/retirement decision, run a fresh prepare/build/pack/seal/stage cycle, recreate the application for changed bind-mounted deployment files, and wait for HTTP readiness before login. Preserve the previous sealed deployment until the replacement's relevant activation checks pass. Changing a setting does not make an earlier sealed pack current, and `--no-build` cannot refresh compiled settings provenance.

**Correlation and remaining limits.** The required bounded reporter search was attempted but GitHub CLI authentication was unavailable. Four equivalent connected-GitHub searches covered open/closed `HostedPages retention` and `"Hosted asset" budget`, at ten results per query; none returned a candidate. This is not proof of uniqueness and does not justify a duplicate/reject disposition. No issue, comment or message was posted. [Correlation record](C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis/artifacts/pdfjs-retention-investigation-2026-10-27/correlation-summary.json).

The reproduced root cause and repair boundary are sufficiently concrete to proceed with a scoped Program Kit plan. Full host/browser qualification of a future repair, its public support seam and the product's intended retirement policy remain to be established. Nothing here marks a repair implemented, released or consumer-confirmed.
