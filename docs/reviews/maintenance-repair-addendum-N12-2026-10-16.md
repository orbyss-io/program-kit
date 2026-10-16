# Maintenance repair addendum: N12 Windows staging cleanup

Prepared 16 October 2026 after approval of the 43-finding maintenance plan. This is a new finding for implementation review, not a retroactive change to the approved scope count or its audit. The approved plan, research review, coverage audit and implementation ledger remain unchanged. N12 adds one distinct finding to track alongside the original 43; the combined inventory is 44 if this extension is adopted.

## Report and source evidence

The ongoing consumer implementation chat reported that native composition update completed selected-root restore but failed deleting its temporary NuGet cache with WinError 145 (directory not empty). The report attributes this to deeply nested package paths exceeding traditional Windows path limits. Its continuation diagnostics records this as D28. A successful restore is not a successful complete update when required cleanup fails.

Read-only inspection of the current Program Kit template confirms ordinary `tempfile.TemporaryDirectory` contexts in `extensions/program-kit-dotnet/templates/dotnet/files/eng/release_bundle.py` for selected-root restore and bundle staging, with long descriptive prefixes. The corresponding repaired consumer code introduces shorter scratch names and an explicit cleanup context. Its regression creates nested paths exceeding 300 characters using extended Windows paths, raises a representative body error, and checks that the body error survives successful cleanup and that scratch is absent.

The consumer reports all nine related bundle tests passing and an actual maintained update rerun in progress. This maintenance chat has inspected code and the report, but has not independently reproduced the original failure, rerun those tests or observed a completed successful update. WinError 145 alone does not prove path length rather than another cause such as a remaining open handle; retain actual failure logs and qualify the real route.

## Assessment of the local repair

Short owned scratch roots plus extended-path deletion are a reasonable direction. The local implementation is not sufficient evidence of a complete reusable cleanup contract:

- Its `finally` block calls `shutil.rmtree` directly. The regression proves preservation of a body error when cleanup succeeds; it does not prove correct diagnostics when both body and cleanup fail. A cleanup exception can become the primary exception while the body error is only chained context.
- Its extended-path conversion prepends `\\?\` to a normal resolved path. UNC paths require different conversion semantics. Qualify UNC only if that location is supported; do not advertise it based on drive-path tests or introduce invalid path strings.
- Checking that a resolved target is somewhere below artifacts does not alone prove that it is still the exact owned scratch directory originally created. A replaced root or reparse target within artifacts must not redirect cleanup to another owned or unrelated directory. Reuse appropriate platform-safe path helpers and make ownership/identity constraints explicit.
- Shorter prefixes reduce depth but cannot establish general long-path support. Real restore/staging operations and cleanup must be qualified under the supported path model.

## Planned upstream work

**Owners:** Program Kit native bundle/staging tooling and central validation. **Related packages:** F/G and the platform-path portion of N2; this is separate from durable witness retention.

1. Preserve the actual restore and cleanup observations separately. Establish the original cause using the failing native route and supported Windows runtime, then repair that cause rather than assuming every directory-not-empty error has one explanation.
2. Provide one owned staging lifecycle used by selected-root restore and release-bundle staging. Use short generated names, verify the absolute artifacts parent and exact created scratch identity, and confine deletion to that scratch root. Never delete an artifacts parent, application directory, durable witness, data or volume.
3. Use supported platform path conversion for cleanup and relevant staging operations. Check containment and ownership before deletion. Handle supported drive/extended/UNC forms precisely, with unsupported cases diagnosed honestly; do not change machine long-path policy or broaden filesystem access.
4. Define dual-failure behavior explicitly. Preserve the original body failure as the primary operation failure and retain an observable cleanup error plus exact residual scratch identity. When the body succeeded but cleanup failed, do not report the overall operation as successful. Never suppress cleanup failures merely to make an update green. Any retry must remain bounded and confined to the same verified scratch identity.
5. Migrate the verified consumer workaround through the normal released updater after central coverage exists, retaining its historical patch/evidence and current business work. Do not alter the active consumer from this addendum task.

## Required closure evidence

| Case | Required observation |
| --- | --- |
| Windows deep package tree | Paths over 300 characters are actually created; owned scratch is removed on normal completion and after a body error. |
| Body and cleanup both fail | Original body failure remains primary; cleanup failure and residual scratch are recorded honestly. |
| Cleanup alone fails | Overall operation reports failure and preserves actionable cleanup evidence. |
| Ownership and containment | Parent/outside/sibling/substituted-root targets are rejected without deleting them; unrelated sentinel files remain untouched. |
| Platform path forms | Supported drive, already-extended and UNC handling is qualified; unsupported forms have a precise disposition. |
| Real integration | Actual maintained selected-root restore and bundle staging complete with cleanup on Windows, with native evidence inspected. Mocked restore or a successful restore record alone is insufficient. |
| POSIX and installation | Equivalent lifecycle remains correct on CI; the packaged/installed template uses the shared fix and validation inventory selects its checks. |

No product code or consumer data was changed by this addendum. The actual implementation chat must record adoption, implementation and validation separately; the earlier 43-item audit does not certify this addition.

## Handoff text for the implementation session

Read `C:\Users\tech_\Code\program-kit\docs\reviews\maintenance-repair-addendum-N12-2026-10-16.md` and assess N12 alongside the approved batch. It records the new Windows selected-root/bundle scratch cleanup defect, the consumer workaround, its remaining gaps and required central evidence. Track it separately from the original 43 findings; do not rewrite their approval or audit. Preserve ongoing implementation and consumer work. Do not blindly copy the workaround: qualify exact scratch ownership, supported extended paths, dual-failure reporting and the real maintained update route. This adds no paid-execution, device-installation or publication authority.
