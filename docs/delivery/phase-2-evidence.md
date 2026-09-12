# Phase 2 acceptance: Azure setup, planning and repository activation

Date: 2026-09-12. Branch: `codex/backlog-delivery`, based on Phase 1 `05fcf1a`.
Status: **Phase 2 complete**, including the real human portal discovery, approved decomposition
and native hierarchy verification. This record accompanies the Phase 2 completion commit.

## Implemented scope

The optional Azure command supports reviewed private Agile project/coordinator creation or
explicit existing-resource attachment, actual per-type field/state and individual identity
discovery, default profile generation, exact-branch permissions, untagged Epic discovery,
reviewed Epic → Feature → Requirement (native User Story) → meaningful optional Task planning,
and per-repository activation for refinement. No installation or upgrade activates cloud authority.

Approved proposal digests and complete native bases precede conditional operations in shared
Azure Git state. Work-item updates test their revision. A lost create response or identity-record
commit remains unresolved until observation finds the exact existing item; the adapter never
replays an ambiguous create. Duplicate correlations, changed fields/links, comment-only revisions,
concurrent adoption and stale coordination heads stop affected work. Automatic parent revisions
are allowed only for the exact new child links and revision count caused by this proposal.
Links are also checked when Azure exposes a parent-link change without advancing its revision.
Recovery also checks untouched fields on existing items. Native HTML normalization is restricted
to the observed whitespace immediately before closing paragraphs.

Activation verifies the immutable policy bytes, current provider registration, native scope,
identity, branch protection and local handoff. Repeating the same decision preserves binding/history.
Refinement checks current accepted Requirement content and planning basis. Existing architecture
and intake gates remain mandatory. Execution claims, complete historical reconciliation, verified
delivery, acceptance, profile change/disconnect and GitHub parity remain later phases.

## Actual Azure resources and results

All cloud mutations used the explicitly authorized private test project; Phase 0 was preserved.

| Resource or case | Evidence |
|---|---|
| Project | [ProgramKit.Delivery.Phase2](https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase2), ID `2dd96afc-aaf1-4cc8-b376-27ea4f84ef03`, private Agile. |
| Coordinator | `delivery-coordination`, repository `5b7a2eba-2850-4198-b38b-83471dc71d5b`, branch `coordination`. |
| Pinned policy | Commit `ce64fa9388c364c015f85c88f4c4462aa25e6310`, `delivery/profile.json`, exact byte SHA-256 `375dab5585d4be6465b7ac436a10fd828ef950eacd9593bc339ac2697d4e22e4`. |
| Scope | Root Area ID `c60f4545-1170-4179-b8bd-7140e74eb721`, path `ProgramKit.Delivery.Phase2`, descendants included. |
| Protection | Exact participating identity ACE allows Read/Contribute (6) and denies ForcePush/ManagePermissions/EditPolicies (10248). Effective permissions checked with administrator allowance disabled. Azure administrators retain recovery power. |
| Final synthetic hierarchy | Run `05644986`, proposal `d459f951-201a-495c-9ace-f37c767e286c`: [Epic 77](https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase2/_workitems/edit/77), Feature 78, Requirement 79, Task 80. |
| Interrupted create | Response deliberately lost after Requirement creation. Recovery found only native ID 79, continued the hierarchy, and repeated apply created no duplicate. |
| Concurrent edit | Separate synthetic Epic 81 changed through an independent API edit after proposal approval. Stale application was rejected and the edit preserved. This was an API fixture, not the user's portal case. |
| Activation | Repository `204d5894-5d90-4ab6-bb22-b999b88e6a43`, team `3839c826-f48b-4911-bb2e-72fdd4a4f19c`, activation `99382a26-3971-4fa0-8786-bd8f09733ad6`. Synthetic local SPC-001 maps to the previously accepted Requirement 74/Task 75. |
| Final installed verification | Updated installed runtime admitted refinement (exit 0), rejected implementation/delivery/acceptance (exit 2), and preserved binding/history bytes. Shared state at `df5c0d235a75b5679b53e8b906c532208f062fef` had **zero unresolved operations**. |

Earlier synthetic hierarchies and deliberately stale approved proposals are retained as evidence;
they are not business backlog. Stale proposals are not silently reapplied or deleted. The initial
pinned test profile predates the generator's descriptive milestone mapping adjustment; its
top-level placeholder is not a native write destination. Per-type mappings and reviewed description
content govern the tested adapter. The current default generator was independently exercised
against the same project and emits `System.Description` for milestone content. The pinned policy
was preserved rather than silently changed under an activated consumer.

## Validation

| Check | Result |
|---|---|
| `tests/validate_delivery_azure.py` | 36 deterministic tests passed: graph/hierarchy, exact approval and roles, native/concurrent adoption, CAS dispatch, pagination, unknown setup/create outcomes, recovery, untouched-field and link/comment preservation (including unchanged parent revisions), milestones, protection, activation and business drift. |
| `tests/validate_delivery.py` | 25 tests passed, including the new empty-Git provenance case and existing core authority boundaries. |
| `scripts/Test-ProgramKit.ps1 -Suite Development` | Passed, including specification intake and existing bounded development regressions. |
| `tests/validate_governance_state.py` | Passed targeted core governance checks. |
| `scripts/build_release.py` | Built local component archives, bundle and checksums; no publication. |
| `tests/validate_release_install.py` | Actual packaged installation passed; Azure command, runtime and schema installed, with delivery still disabled/unconfigured. |
| Product default-profile generation | Passed live read-only field/state/identity verification against the existing authorized project. |
| Synthetic Azure probes | Final hierarchy/recovery/concurrent-edit run and final installed activation verification passed. No coding-agent sessions were started. |
| Real human portal journey | Epic 82 was discovered untagged, explicitly reviewed, and decomposed into Feature 83, Requirements 84–86 and Task 87. Original human content/provenance preserved; repeated apply changed no operational state. |

Logs and detailed JSON are retained under ignored `artifacts/delivery-phase2/` in the worktree:
`development-verified.log`, `governance.log`, `package-build.log`, `package-install.log`,
`live-probe-final.log`, `runs/final-revision-guards/results.json`,
`activation-final-verification.json`, `activation-final-verification.log`,
`generated-default-profile.json`, setup/protection journals and earlier attempts.
Final completion checks after the same-revision parent-link correction are retained in
`development-human-complete.log`, `package-build-human-complete.log`,
`package-install-human-complete.log`, `human-epic-82-final-results.json`,
`human-epic-82-final-verification.log` and `activation-parent-links-verification.json`/`.log`.
The final activation JSON records hashes of all tested installed governance/delivery source files.
The initial activation consumer is retained at
`C:/Code/Orbyss/_ProgramKit/artifacts/d2activation/consumer` to avoid Windows path-length limits.

Local package SHA-256 values: delivery archive
`1eea745cac1db1547271deffd053fe124b3db14c5cd9b48dc16cf01e3e33de67`, bundle
`be17350a51cdb79d6aae99e8c092b83ed6eb4208846243bb4d028256eb287e44`.
These are development package checks, not Release receipts or published artifacts.

The first native dry run rejected AssignedTo GUIDs before creation; dispatch now resolves the
verified identity to its native account while approval/recovery retain the stable ID. An earlier
interrupted Requirement 70 was recovered after observing Azure's HTML whitespace behavior and
the remaining Task was created. Original failed-run evidence remains intact.
Two activation fixture copies exceeded Windows path lengths before activation; a shorter artifact
path resolved the fixture limitation. Live Azure TLS uses system Python 3.12 because the installed
Spec Kit Python 3.13 hits the known host `OPENSSL_Applink` failure during TLS setup. Deterministic
Development/package tests used Spec Kit Python 3.13. Production TLS checks were not weakened.

## Completed human acceptance

Update: the user confirmed creating [Epic 82: Implement Customer Service Pilot](https://dev.azure.com/Unfussiness/ProgramKit.Delivery.Phase2/_workitems/edit/82)
in the portal. Product discovery found it in scope at revision 1, created at
`2026-09-12T19:13:00.09Z` by the verified user identity. It has no tags or assignment and its
description is preserved: manual customer interaction and DevOps ticket creation should become
automated request intake, scope assignment and item creation in the appropriate project/area.
This confirms that neither tags nor assignment are required for discovery.

The user explicitly approved proposal `40b028dc-597c-4276-9115-b08860faaa6e`, SHA-256
`cd4b414c96d8ba019d5e9ef11db6f31b68062562cff700dc262747bc127ee985`, assigning the
existing Epic to its human owner, one Feature, three Requirements and one receiving-integration
Task. It preserves the Epic title/description and explicitly leaves channel, routing rules,
target item type and implementation architecture unresolved for refinement. The user approved
the proposed ambiguous-request review behavior and duplicate-prevention criteria with the graph.
Artifacts: `human-epic-82-discovery.json`, `human-epic-82-entries.json`,
`human-epic-82-proposal.json`, `human-epic-82-proposal.md` and their logs in the evidence directory.
Approval rechecked the revision-1 basis. Application assigned the Epic to its human owner and
created the approved native hierarchy:

- Epic 82 → Feature 83: Route pilot customer requests into Azure DevOps.
- Feature 83 → Requirement 84: Receive a customer request for pilot processing.
- Feature 83 → Requirement 85: Resolve the DevOps project and area for a customer request.
- Feature 83 → Requirement 86: Create and trace the routed customer request in Azure DevOps.
- Requirement 86 → Task 87: Verify the pilot receiving integration with Azure DevOps.

Verification compared the actual types, scope, parent/child links, assigned owner and reviewed
fields. The Epic's title, exact description, creation identity/time and comment count are preserved.
Repeating the approved apply created nothing and left shared commit
`afd40aae3967cc64ca26c49613fa5e4ddf031b8c` unchanged, with zero unresolved operations.
The test exposed native parent links without a parent revision increment; the guard now checks
those links and associated business fields regardless of revision, with two additional regressions.
The final human verification and installed activation check passed with that correction.

This validates the backlog-management journey, not implementation of the Customer Service Pilot.
The Task is a future integration-test obligation, not proof that the pilot already works.
Hold the Phase 3 grilling interview before starting reconciliation implementation.
