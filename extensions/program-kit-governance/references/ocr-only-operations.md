# Bounded OCR-only provider operations

Use this optional path when existing broad provider/model acceptance correctly
rejects a one-page OCR-only operation. It does not weaken that gate or supply
combined provider, model, application or paid coding-worker acceptance. Native
compatibility evidence is a prerequisite; it is not consent to spend.

The selected native adapter uses public Azure.AI.DocumentIntelligence 1.0.0,
prebuilt-read, API 2024-11-30, pages=1, text output and zero SDK retries. A physical
request gate admits exactly one matching POST with the immutable input bytes.
Recovery uses the public GetAnalyzeResult/DeleteAnalyzeResult REST contracts with
the original Read result GUID. It never resubmits. Redirects, cookies, fallback
models and automatic polling are disabled. A DELETE acknowledgment supplies no
absence claim; a separately authorized GET must observe absence.

Prepare the adapter explicitly with the installed governance script:
`python .specify/extensions/program-kit-governance/scripts/provider_operation_prepare.py --repository .`.
This acquires only public SDK packages, restores the maintained lock in owned
neutral build policy, runs the recording cases and retains a hashed native
payload/receipt. Execution checks that receipt, current adapter/mechanism sources,
payload and actual installed runtime without building, restoring or acquiring.
A missing/stale preparation requires explicit preparation again; retain originals
needed by existing recovery. Never rewrite a prior receipt to make it current.

The human initializes one original local resource account with the same script's
`--initialize-account --resource <Azure-resource-id> --ceiling-micro-usd <integer>
--historical-reservations <contained-json-path>` options. The historical input is
an explicit array of `{path, sha256, reservationMicroUsd}` original records; review
all prior uncertain operations before asserting an empty array. This terminal
step requires the displayed full confirmation. Authority lives under
`.program-kit/provider-operation-accounts`; private accounting lives under
`artifacts/provider-operations/private`. Preserve both across sessions. Losing
private state is an unresolved account, never a new budget. Copied account state
is historical and cannot spend from a second physical directory. Original
history mappings remain hashed and fully charged.

The exact JSON operation contract is validated by `provider_operation.contract`.
Declare schemaVersion=1, operation=ocr-read-only,
adapter=azure-document-intelligence-1.0.0-read-v1, the reviewed resourceIdentity,
public HTTPS account endpoint, fixture `{path,sha256}`, adapterPreparation
`{path,sha256}`, original account `{identity,authorityPath,authoritySha256}`,
credentialRef (environment variable name only), preparedAt, submitBefore and
recoverBefore. Its closed `limits` object requires submissions=1, pages=1,
modelCalls=0, sdkRetries=0, fallback=false, maximumInputBytes,
maximumResponseBytes, timeoutMilliseconds, pollTimeoutMilliseconds, polls,
deletions, runReservationMicroUsd and aggregateCeilingMicroUsd. Input/response
caps are at most 1 MiB, one reservation at most 10,000 micro USD, submission
permission at most one hour, recovery at most one further day. Unsupported fields,
booleans in integer fields, aliases and broader operations fail before admission.
The reservation must conservatively cover the complete operation's possible cost;
this local accounting is not a provider pricing quote or billing reconciliation.

Use the existing native compatibility prerequisite/recipe owner to bind the exact
contract, fixture, original account authority and adapter receipt as proof inputs.
It must pass its actual named runtime/JUnit checks and remain the current native
admission. The human then runs `provider_operation_authority.py --repository .
--contract <path> --prerequisite <id> --recipe <path> --output <new-manifest-path>`.
It displays original history, all retained attempts, totals and limits, and requires
the complete exact confirmation line. Never run this interactive issuer or original
account initialization from an agent, CI or hook. There is no approved/yes flag.
Local attestations are attributable records, not cryptographic person identity.

`provider_operation_execute.py --repository . run --contract <path>
--authorization <manifest> --prerequisite <id> --recipe <path> --execution provider`
consumes that exact one-use manifest and reserves the full amount atomically before
possible POST. Concurrent native processes share the original aggregate ceiling;
uncertain, unavailable and cleaned-up attempts remain charged. Only the native
provider child receives the exact credential reference's value. Recording-mode
manifests are explicitly fictional and cannot authorize provider execution.

Recover with `provider_operation_execute.py --repository . recover --resource
<original-resource-id> --attempt <uuid> --action poll` (or delete). Recovery validates
original manifest/proof/report bytes and the archived operation, consumes only its
original action count and deadline, and retains known handles immediately before
later response work. No handle means investigate the uncertain operation without
resubmission. A newly issued manifest never renews an existing attempt's limits.
Private results are retained separately; event/process evidence contains hashes,
safe status and bounded redacted streams. Cleanup of provider state does not erase
local private result files or create additional spending capacity.

The deterministic `tests/validate_provider_operation_accounting.py` exercises actual
native admission, the public SDK and separate native processes using recording
HTTP only. Required SDK and execution case inventories reject omissions or
substitution. No socket/provider/model call, human consent or application acceptance
is claimed. The local SQLite/hash-chain mechanism excludes hostile writers,
authority/history backup rollback, shared network storage and multiple hosts.
Byte caps and cooperative cancellation do not establish OS CPU/memory limits.
An unreachable provider, crash, malformed result or expired deadline remains
unknown/unavailable, with original reservations and recovery evidence preserved.
