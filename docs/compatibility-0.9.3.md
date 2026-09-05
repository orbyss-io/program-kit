# Program Kit 0.9.3 compatibility report

0.9.3 is a compatible upgrade-safety correction. Application runtime APIs and the exact `PKA014`
producer policy do not change. Existing repositories without registered OpenAPI contracts, or whose
contracts already match the target exporter pin, retain the normal sequential updater behavior.

An upgrade with stale registered Program Kit exporter pins now requires explicit reconciliation.
The first updater run exits with code 2 and `PKU110` before any component or consumer mutation. After
review, rerun the same release updater with
`--accept-openapi-producer-pin-reconciliation`. Consumer-owned changes are then explicit and atomic;
custom producer kinds, malformed contracts, downgrades, and active lifecycle operations remain
manual blockers.

When reconciliation is applied, the updater completes component/version convergence but exits with
code 3 and `PKU111` because implementation readiness was intentionally invalidated. This is a
required continuation state, not permission to bypass the hook. Run `$speckit-analyze`, the Program
Kit architecture check, and the Program Kit implementation check for every feature named in the
diagnostic. Successful renewal creates new artifact hashes and analysis evidence for the reconciled
contract and planning bytes.

For the already-remediated PriceCalculator case, updating the contract plus all exact planning and
research references, renewing analysis, and rerunning governance/lifecycle/artifact ownership is the
safe immediate path. Those checks currently pass on its 0.9.2 state, so it does not need to bypass
`PKA014` or wait for 0.9.3 to continue implementation.
