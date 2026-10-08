# Dependency context repair, 2026-10-08

This is a source patch to main at 42ea361e54b341caa922f76b3d62bd42faf54b67.
VERSION remains 0.12.9. No tag, publication, Release suite, or coding-agent worker
was started. Historical dependency profiles, evidence and consumer locks remain
unchanged; the personal untracked .agents directory is preserved.

## Implemented behavior

The building-block resolver now exposes effective_dependency_context. It verifies
captured Draft/Accepted catalogs and immutable profiles first, recorded scaffold
authority before selection capture second, and the qualified default for genuinely
unbound consumers. Legacy installations retain their installed catalog. Invalid
captures, scaffold hashes, qualifications or publisher/ABI provenance fail with a
scoped repair instead of choosing another dependency profile.

Runtime and capability projections, engineering pins, provider research,
compatibility scopes, recipe generation and both ownership audits use this
context. Matching publisher knowledge requires the complete catalog tuple,
including independently versioned Build, exporter, Forms and Localization.
Interrupted upgrade inspection passes its already recovered old catalog through
the same verifier; installed replacement bytes cannot supersede that authority.

Qualification and consumer recipes share project-pin preparation and public Host
capture. Both maintained recipes render the selected Foundation and shared ABI
pins. Foundation 0.3.x uses the reviewed Host/shared-binding protocol and disables
scratch package pruning. BFF/Keycloak separately exercises its own activation and
browser mechanism. Exact Host and Keycloak images are provisioned without relying
on a warm image cache. Scratch preparation rejects mixed profile, release, ABI,
project pins and restore policy before native provisioning.

Generated briefs bind profile resolution and all verified authority sources.
The evidence index retains individual source hashes without inflating worker
briefs beyond their existing 32 KiB bound. Normal workflow build steps regenerate
derived context before dispatch; validation continues rejecting stale context.
Current summaries come from structured selected facts. A contradictory current
Host claim in technology-radar.md produces DEPENDENCY-SUMMARY-CONFLICT and names a
scoped tooling review. Historical release examples no longer supply a current tag.

## Verification

The new effective-context validator covers fresh defaults, recorded scaffolds,
retained legacy selections after kit updates, Draft/Accepted continuity, all six
added capabilities, all seven newly managed NuGet identities, planning and
materialization ownership, mixed qualification/ABI authority, stale summaries,
source binding, and both recipe preparation paths. Retained 0.2.4 and 0.3.0
recipes are checked for their exact pins and different protocols.

Native consumer-path evidence is preserved under
artifacts/consumer-provider-runtime/1a93086b/. Both independently passed:

- foundation-activation: five compiled boundary, exact-image activation,
  registration/replacement, HTTP/OpenAPI and restart cases.
- bff-keycloak: exact provider discovery, published BFF activation, and browser
  code flow with permission negatives, cookie/storage and logout assertions.

These are synthetic mechanism checks. They do not close an existing consumer's
source-bound prerequisites or establish feature behavior, production identity,
redistribution acceptance or public availability of this patch.

The final Development journal at
artifacts/validation-runs/20261008T162921Z-0ab5d8f4/journal.json records all 81
checks passing. Earlier failed journals remain preserved: the engineering-pin
test's obsolete resolver mock was replaced with real captured profiles, and
Windows temporary-file replacement contention was resolved for validation by
using the normal user temporary directory and the exact prepared toolchain.
No production workaround, retry relaxation or validation gate change was added
for those host failures. Targeted journaled reruns are also preserved.
Additional focused checks cover bootstrap context/staleness and bounded briefs,
provider handoff, dependency audit/profiles, interrupted exporter upgrade,
placement contracts, proof-plan ownership, shared compatibility, validation
inventory and the 67 Host binding guard groups. Firefox remains a known local
host limitation and remains in CI; this patch establishes no Firefox acceptance.

## Existing consumer update path

No notes_app files were edited. A read-only observation confirms its selected
Host is 0.3.1, selection hash remains
026e04106f6e469f698197c9217d2ae5d2b1dfb459a483ea39a70445f024d0c2,
and the accepted fd-browser-identity ADR still matches its architecture-map hash.
The radar still claims Host 0.2.2; external-host-bff remains open before
implementation. artifacts/dependency-context-consumer-observation.json records
the observation. The exact observed image digest remains
sha256:8abe8dd28b1b99ac316f811dcd547f02da1f8b664dceb376feff4c0cb7cbfede.

1. Install the coordinated patched toolkit through its normal local updater,
   preserving selection/profile snapshots and historical receipts. From the kit
   checkout, preview the same-version update first:

   ```powershell
   python scripts/upgrade_program_kit.py --release-root . --target C:/Users/tech_/Code/Orbyss/temp-tests/notes_app --plan
   ```

   That read-only preview was verified: 0.12.9 to 0.12.9, no migrations and no
   mutation. For an explicitly chosen local source installation, remove --plan;
   this installs toolkit files and performs engineering checks, not publication.
   A kit update does not authorize selecting newer consumer dependency pins.

2. Use the existing accepted-bootstrap continuation/review path for the stale
   tooling summary and open compatibility obligation. In the consumer's normal
   terminal, preparation is:

   ```powershell
   python .specify/extensions/program-kit-governance/scripts/bootstrap_recovery.py prepare --run-id 6e921f75 --post-bootstrap
   ```

   Preserve the Accepted selection and corrected ADR. Reconcile the radar from
   selected structured facts, synchronize its registered documentation digest,
   and review the resulting scoped packet. Never rewrite old approvals or proof
   receipts to bless changed bytes.

3. Generate fresh recipe identities with the installed
   managed_compatibility.py render command, separately selecting
   --kind foundation-activation and --kind bff-keycloak, each with --id and the
   exact registry-verified --host-image above. Provision the selected SDK,
   Node/npm and Chromium. Review the continuation's proof plan so both mechanisms
   are required before external-host-bff closes; retain the affected slices if
   that combined obligation is split into two reviewed prerequisites.

4. Run the source-bound proofs through the existing coordinator and finish the
   continuation's human review. Renew only affected receipts under current
   tooling and selected inputs. Rerun implementation source preflight after the
   continuation completes. The kit's synthetic receipts cannot be substituted
   for these consumer receipts.

Consumers that intentionally change dependencies must use the existing explicit
dependency-transition/qualification path. Copying the newest registry default
over a captured profile is not an update path.
