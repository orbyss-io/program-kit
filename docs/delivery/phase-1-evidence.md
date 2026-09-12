# Phase 1 acceptance: optional delivery foundation

Date: 2026-09-12. Branch: `codex/backlog-delivery`. This record accompanies the Phase 1 implementation commit. The branch incorporated committed main `33b69e5` before implementation; unrelated working files in the original checkout were not imported. No release or cloud activation was performed.

## Result

The normal distribution and sequential updater include `program-kit-delivery`, disabled by default. It provides profile/binding/history/work schemas, proposed Azure/GitHub mappings, four content templates, guided configure/refine commands and deterministic offline validation. Consumer binding/history/profile files remain outside installed extension content and are checked for byte preservation during upgrade.

Core roadmap readiness, feature-intake confirmation/checking and direct implementation preflight consult the same delivery authority boundary. Prepared records retain existing local governance; enabled records require provider admission and explicitly report `PKD_ADAPTER_UNAVAILABLE` in Phase 1. Local roadmap projections cannot assert cloud delivery status. Malformed/missing records, changed binding/profile hashes and altered committed history fail explicitly. A hand-written disconnect cannot restore local authority.

Draft epics accept three business inputs. Refinement does not require a technical plan; implementation content requires accepted business/artifact digests and the necessary owner, verification and coordination information. Changed business scope or architecture prerequisites invalidate that content basis. Direct Requirement execution and delegated meaningful Tasks are mutually exclusive in the contract. Content validation never grants an execution claim or proves provider evidence.

## Validation

All checks are deterministic and start no coding-agent sessions.

| Check | Result and scope |
|---|---|
| `tests/validate_delivery.py` | 24 tests passed: disabled behavior, installed CLI, prepared/connected records, Git deletion/history checks, profile/binding mismatch, malformed input, minimal epics, separate refinement/implementation requirements, stale basis, Task decomposition and direct core/preflight admission. |
| `scripts/Test-ProgramKit.ps1 -Suite Development` | Passed the bounded Development suite, including delivery and existing specification/bootstrap regressions. |
| `tests/validate_specification_intake.py` | Passed again after the final admission check was added to reuse of an existing confirmation. |
| `tests/validate_governance_state.py` | Passed existing core governance regressions with the new authority seam. |
| `tests/validate_local_upgrade.py` | Passed real sequential offline upgrades, including old consumers without delivery, preserved prepared binding/history/profile bytes, partial-upgrade recovery and lifecycle invalidation/renewal. |
| `scripts/build_release.py` | Built local component archives, bundle and checksums, including the new delivery archive. This is packaging verification, not publication. |
| `tests/validate_release_install.py` | Passed actual packaged installation, generated command registration, disabled/unconfigured delivery, unchanged mandatory hooks and the four-extension bundle graph. |
| `tests/validate_live_bootstrap_acceptance.py` | Passed with system Python 3.12; verifies deterministic receipt/harness contracts including the new candidate artifact. No live acceptance was invoked. |

Local logs are retained under ignored `artifacts/delivery-phase1/`: `delivery.log`, `development.log`, `specification-intake.log`, `governance.log`, `local-upgrade.log`, `package-build.log`, `package-install.log` and `receipt-contract-py312.log`. The Spec Kit Python 3.13 interpreter hit host `OPENSSL_Applink` failure in the receipt/harness test; the independent system Python run passed. No production workaround was added.

The older upgrade fixture predates mandatory feature intake from main. It now verifies the full preflight rejects missing intake, while retaining direct lifecycle checks that stale analysis blocks implementation and renewed analysis restores lifecycle readiness. Dedicated intake/delivery tests verify those earlier gates. Production gates were not weakened.

## Remaining phase boundaries

Default profiles are proposals with explicit setup placeholders, not verified resource identities. Phase 2 must discover and validate Azure capabilities, implement accepted activation and resumable approved writes, and bind the existing roadmap identities to the provider. Reconciliation, execution claims, receiving integration evidence and GitHub parity remain their planned later phases. Historical Phase 0 receipts are unchanged and are not represented as tests of this product code.

Git provenance checks detect ordinary deletion or changes against available committed history; they do not protect against rewriting all history or prove absent provenance in an incomplete clone. Phase 1 has no production activation/disconnect writer, provider permission verifier or execution-claim service. Full Release acceptance remains a later user-owned publication gate.
