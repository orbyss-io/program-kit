---
description: Inspect or apply explicit engineering setup changes.
scripts:
  py: scripts/repository_sync.py
---

Use setup synchronization when adding or changing actual project, package or composition inputs.
It is not a prerequisite for specify, plan, tasks or source implementation. Run `{SCRIPT} plan
--phase implementation --feature-dir <feature>` for an inspectable preview, then `{SCRIPT} apply
--phase implementation --feature-dir <feature>` to compute and apply mechanical metadata.
An optional --plan-digest protects an externally inspected plan against intervening changes.
Only initial bootstrap retains its explicit accepted-setup authority contract.

Use native restore/build/test commands under eng/ for normal engineering. Source/package conflicts,
provider transitions, registry permissions and trust failures need their actual diagnostic resolved.
A missing receipt or changed document bytes do not establish an application problem. Do not write
per-feature success attestations, recovery dossiers or duplicate package declarations.

Routine upgrades use the release-owned upgrade_program_kit.py command; it performs deterministic
setup and dependency verification in one operation. It does not run bootstrap or a coding agent.
An offline upgrade reports any dependency verification still pending separately.

For an explicitly selected supported foundation composition, synchronization materializes
configuration and feature-owned registration/provider seams through the same preview/apply
ownership flow. Link `docs/architecture/foundation-configuration.md` and the redacted settings
view. Materialization alone establishes neither runtime readiness nor product acceptance.
Run maintained `eng/foundation_setup.py` only through explicit service/setup authorization;
inspect its selected inputs, restore/build, actual activation and applicable setup test outcomes.
Do not start it from task drafting, intake or an ordinary hook. Use its named repair for failure
instead of scheduling a generic compatibility-research phase. Preserve captured profiles and
consumer-owned configuration; apply updates through the existing reviewed upgrade mechanism.
