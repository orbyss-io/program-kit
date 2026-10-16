# Proposed N15: physical fencing for durable cross-resource work

Prepared 16 October 2026 from the active consumer implementation chat, its continuation diagnostics and read-only inspection of current consumer source/tests. N15 is a distinct proposed addition beyond the combined 46-finding inventory. Adoption would bring that inventory to 47. It is not retroactive approval, implementation or evidence that Program Kit supplied the defective consumer code. Original plans, audits and the active implementation ledger remain unchanged.

## Observed problem and attribution

The consumer report D38 records a native failing case in which a paused producer published an original file after erase. The later chat update also identifies stale removal damaging a newer lease unless the physical object retains a monotonic fence. The consumer repair is in progress; its complete outbox and SQL reservation lifecycle has not been independently verified here.

Current `Evidence.Files/PolicyEvidence.cs` has a public work-admission path, retained work/operation identity and fence, a short cross-process publication/removal guard, a removal marker, and checks around final file publication and erase. Its current tests include newer-fence rejection of old publication/removal/legacy calls, restart rejection, corrupt fence denial and deadline checks after input or lock waits. These are inspected implementation and test definitions, not independently executed acceptance results. A fresh service-provider registration in one process is also narrower evidence than an actual process restart.

Current Program Kit persistence guidance already requires durable operation identity, an admitted outbox, idempotent receivers, and honest commit uncertainty. That is sound general guidance. Inspection has not established an existing Program Kit implementation or generator responsible for this consumer race. The maintenance opportunity is to make cross-resource physical-effect fencing explicit in relevant guidance and representative regression recipes, and correct a concrete shipped example only if source attribution establishes one.

## Mechanism and critique of the repair

A database completion fence cannot, by itself, revoke a filesystem mutation already proceeding elsewhere. A lease-expiry check before an operation also leaves a pause between check and effect. Resource-side enforcement of increasing fencing tokens addresses stale requests: [Kleppmann's fencing discussion](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html). An [outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) coordinates committed intent and delivery; do not infer an atomic transaction spanning database and arbitrary file effects.

The reported short guard, retained fence and barrier are a plausible local-storage design, but each claim needs proof:

- The fence check and physical mutation must be serialized with admission of a newer fence at the same resource boundary. Keep slow streaming outside that short critical section where supported; recheck identity, fence, barrier, cancellation and actual deadline after waits. A timestamp check does not replace resource-side fencing.
- Every lease-driven read/reconciliation or mutation must establish the intended physical authority before acting. This does not mean all ordinary read-only inspection globally needs a work lease. Precisely identify which observations can authorize later effects and how stale observations are rejected.
- Retain exact object, work and operation identity with a nondecreasing high-water mark across retries, reclaim and restart. Deny missing/corrupt/ambiguous authority where a protected original or stale worker may exist. Same-token replay is allowed only by its explicit idempotency contract; a different work identity cannot reset authority merely by presenting another counter.
- Stale erase requires the same protection as stale publish. Do not let an older cleanup path, overload, reconciliation task or legacy unfenced API bypass the fence. Removing data must preserve the metadata necessary to stop resurrection.
- Barrier/high-water retention needs a proven retirement condition covering outstanding workers, originals, staging, replay and backups that are in scope. A TTL or a completed database row alone cannot establish that no stale producer remains. Prevent counter reuse/overflow and object-identity reuse from resetting the protection.
- Local file guards have a storage/process scope. Qualify their semantics on supported Windows/Linux filesystems and any shared-volume arrangements actually advertised. Do not infer multi-host, network-filesystem or object-store guarantees from a process-local or local-filesystem test.
- Process-crash consistency and power-loss durability are distinct claims. File flushing and atomic rename alone are not proof of every supported crash/power-loss outcome. Keep unqualified durability and hostile-local-process assumptions explicit; retain privacy-safe metadata only as needed by the accepted retention policy.

## Planned upstream handling

**Owners:** Program Kit persistence/background-work integration knowledge and central representative examples; a native publisher extension only if an attributable reusable contract gap is established. Consumer SQL schema, business lease/reclaim policy, document removal semantics and domain worker tests remain consumer responsibilities.

1. Trace the relevant selected guidance and any generated task/example before assigning a Program Kit defect. At the point where cross-resource durable work is designed, require an effect inventory and explicit ownership of publication, reads used for reconciliation, erase, replay and cleanup.
2. Add a bounded reference recipe showing committed work identity, increasing lease fence, resource-side admission/mutation, retained removal protection and recovery after uncertain effects. Use existing public seams; do not create a generic storage framework or copy the consumer's domain implementation solely for this finding.
3. Require the recipe to state its platform/storage scope, authority and retirement rules, uncertainty classifications, supported replay behavior and durability limits. An uncertain physical effect remains reconciliation work, not a reason for blind resubmission, new paid execution or fabricated cleanup success.
4. Centrally exercise a minimal synthetic implementation that proves each shared claim. Keep actual domain-specific PostgreSQL/file transaction and end-to-end business cases in the consumer, without duplicating its full suite.

## Required closure evidence

| Scenario | Expected proof |
| --- | --- |
| Paused producer, erase, resume | Original cannot be published after the retained removal barrier; only owned staging is cleaned. |
| Reclaim with a higher fence | Old producer and old remover cannot affect the newer object's state; matching replay is explicitly bounded. |
| Restart and recovery | Actual supported process restart preserves high-water identity and rejects old authority; inspect physical and database state independently. |
| Legacy bypass | All relevant old/unfenced paths reject protected operations rather than resetting state. |
| Waiting and expiry | Check after input/guard waits, including deadline equality; a newer fence remains authoritative regardless of old process timing. |
| Corruption and identity reuse | Missing/duplicate/corrupt fence records and different work/object identities fail honestly; no reset-to-zero recovery. |
| Crash windows | Interrupt between intent, fence persistence, physical effect and completion; preserve uncertain effects and reconcile without duplicate effects. Advertise only tested durability. |
| Retention and removal | High-water/barrier retirement cannot resurrect work; privacy/cleanup claims distinguish content removal from retained opaque metadata. |
| Platform and concurrency | Real cross-process contention on supported Windows/Linux storage; unsupported shared/multi-host storage receives an explicit limitation. |

**Closure:** an attributed guidance/example repair or precise disposition, meaningful central recipe evidence, and explicit consumer/publisher boundaries. The consumer's repair remains in progress and is not declared correct merely because matching source/tests now exist.

## Handoff

Assess N15 for adoption after the existing approved work. If adopted, record it separately in the implementation ledger and bring the combined inventory to 47; preserve original approval/audit history. Review the consumer remedy critically, especially resource-side enforcement, stale erase, restart, high-water retention and legacy bypass. This research changes no product/consumer code and grants no publication, paid-call, paid-worker or destructive-data authority.
