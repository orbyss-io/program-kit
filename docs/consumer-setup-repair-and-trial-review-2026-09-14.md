# Consumer setup repair and trial review — 2026-09-14

## Result

The dependency ownership audit and implementation entry sequence are repaired. The
installed older consumer passes the repaired dependency audit; its bootstrap still
returns `completed` with `engine_verified: true`. Its feature was **not ready for
application coding**: its planned direct dependency graph still needed correction.
At the operator’s direction, that consumer is now historical learning only and will
not be resumed. The findings are retained to improve future flows.
The next fresh trial is Household Shopping. Repair Desk and its interrupted intake
are superseded at the operator's request; disregard the Zendesk direction.

## Confirmed defects and repairs

1. **Circular implementation entry.** Preflight required materialized persistence
   projects before the documented skeleton step. The explicit `--stage setup` now
   checks confirmed intake, analysis, planned ownership, selected dependency bindings,
   planning context and design obligations. It permits only approved skeleton setup.
   `--stage source` (the default) requires actual references, implementation sync,
   current restore evidence and materialized persistence before application coding.
2. **Conflicting dependency ownership.** The audit understood only a building-block
   lock, so it rejected the engineering baseline's own OpenAPI tool. It now checks
   the exact managed receipt AND rendered installed template. The former unconditional
   engineering central-pins path exception is replaced with the same hash checks.
3. **Retained proof inputs treated as application dependencies.** Current bootstrap
   prerequisite validation supplies exact hash-bound inputs; strict graph validation
   supplies the isolated feature candidate. The audit and restore inventory share this
   classification. It is not a docs/specs directory exclusion. Changed inputs, unowned
   projects, active selection/runtime targets, ProjectReferences, MSBuild imports,
   solution inclusion, npm local dependencies and npm workspaces remain rejected.
   No-op materialization checks also audit for newly added unmanaged references.
4. **Masked resolver error.** ResolverError was a frozen dataclass, preventing the
   generator context manager from assigning its traceback. It now propagates the
   original diagnostic. The regression exercises a real context manager and failed
   materialization rollback, not merely a writable-attribute assertion.
5. **Dirty test payload.** Intake archives included local `bin`/`obj` build products,
   unlike release archives. Intake now uses the existing deterministic release archive
   function, preserving its strict reparse guard. A test proves that adding local build,
   package, browser-result and auth outputs does not change the candidate archive.
6. **Local archive transfer instability.** PrepareOnly exposed repeated incomplete
   localhost downloads with WinError 10054. Direct urllib and curl reproduced the
   transfer problem outside Spec Kit. Alternating the same archive through 1 MiB and
   64 KiB file-copy writes observed a timeout with 1 MiB and successful exact bytes with
   64 KiB. The intake-only server now bounds writes to 64 KiB. No consumer proxy, TLS,
   firewall or global networking setting changed. This is bounded local evidence,
   not a complete explanation of the Windows networking failure or a universal guarantee.

## Other findings in the older feature run

- Planning/delivery assignments P01/P02 were initially classified as unresolved
  deferred decisions. That caused a needless reconfirmation; the consumer agent
  corrected it. Distinguish assigned work from an unanswered decision during review.
- The feature graph lists inherited Foundation.Analyzers as direct references in ten
  projects. ProgramKit.Build.props already supplies that repository-wide reference.
- LifecycleDelivery plans Tasks and Tasks.Abstractions without a selected composition
  bound to that project. The catalog already supplies `background_tasks`; a new
  instruction or consumer implementation of the framework is not the remedy.
- API tests plan direct Json/WebDefaults references without corresponding target
  ownership. Review which references tests actually need before amending selection.
- New PKA016 planning checks identify these missing bindings before skeleton creation.
  This does not silently add a composition, approve a decision or expand compatibility
  proof claims. An accepted selection amendment changes source-bound proof authority;
  retain old receipts and follow the required review/renewal route.
- Repeated large source/context outputs are an efficiency concern: the feature window
  contains 786,926 serialized tool-output characters and 12 outputs marked truncated.
  This is an observable reading-volume signal, not a measurement of wasted tokens.
  The run also rediscovered existing package-access infrastructure and briefly included
  its own review receipt in its verification inputs. Both caused avoidable work and
  were corrected by the agent. Broader context-routing improvements remain review work.

The interrupted Repair Desk attempt never reached confirmed intake or bootstrap.
Its business direction was changed by operator misunderstanding, explicitly withdrawn
by the operator. Do not score that direction as a Program Kit product defect. The
agent correctly kept unanswered factual questions open despite broad acceptance of
recommendations. Its reading volume remains useful operational evidence.

## Measured usage, with limits

| Observed window | Input | Cached input (subset) | Output | Uncached input + output |
| --- | ---: | ---: | ---: | ---: |
| Older feature flow, 21:03:20–22:36:05 UTC | 12,521,163 | 12,169,472 | 51,184 | 402,875 |
| Interrupted Repair Desk intake | 575,357 | 530,688 | 11,239 | 55,908 |

These are deltas from retained session token counters, not new model runs. The older
window includes the correction/confirmation interruption. Wall intervals include
human waiting. Cached tokens are not free and are not added twice. No currency cost,
productive/wasted time split, or comparative improvement percentage is claimed.
The scopes and completion states differ; neither window represents a delivered app.

## Verification and preserved evidence

- Bounded Development suite passed: `artifacts/dependency-audit-development.log`.
- Subsequent focused checks passed after the final local-server/guard changes:
  19 intake launcher tests, 6 dependency audit tests, discovery fixture isolation.
- Offline replay materialized eight outputs twice with identical results and preserved
  all 500 protected files copied into the replay. No network restore or agent ran.
- Supported extension installation into the older consumer preserved all 598 protected
  files in place; installed audit passed and engine completion was reverified.
- Fresh Household Shopping PrepareOnly passed all eight install steps:
  `artifacts/intake-sessions/4a62f45f493e4afd8098938b26d5d237/`.
  Installed repair hashes match source; generated implementation skill has both stages.
  No acceptance folder, confirmed intake, workflow run or coding-agent session exists.
- Earlier failed setup attempts and transfer comparisons are retained. Do not count
  their corrected sequence as first-pass success.

Detailed local-only evidence is under `artifacts/dependency-audit-repair/`, including
trial-metrics.json, consumer-replay.json, consumer-installed-verification.json,
consumer-protected-before.json, consumer-protected-after.json,
shopping-installed-hashes.json and loopback-buffer-comparison.json. Keep private
consumer transcripts and credentials out of commits and publication.

See [the restart guide](household-shopping-restart-2026-09-14.md) for the next action.
