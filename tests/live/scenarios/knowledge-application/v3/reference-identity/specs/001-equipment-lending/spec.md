# Equipment lending reference behavior

- **Specification roadmap entry**: RM01
- **Specification identity**: equipment-lending/v1
- **Status**: documented reference implementation; governance remediation required

This hand-authored record describes the independently tested reference. It is not
an assertion that Spec Kit generated this spec or that a human confirmed an intake.
No intake confirmation, bootstrap approval or constitution ratification is supplied.
The canonical model alongside this document is a proposed target architecture for
review. The legacy implementation uses a plain TypeScript browser and a small API;
it has not adopted the candidate's selected Forms/CShell mechanisms.

The operator reserves one of two cameras, acknowledges confirmation explicitly,
and can cancel a reservation. Policy denial and illegal transitions do not alter
stock or enqueue notifications. A repeated operation retains its operation and
reservation identities. Conflicting reuse is rejected. Accepted records and pending
notification retries survive a real process restart. The durable fictional test
sink records a completed notification once; no distributed exactly-once claim is made.

The public V1 contract retains `operationId`, `equipmentId`, `quantity`,
`reservationId` and `state`. RM02 reporting remains future. Upgrade must retain this
spec's path and identity and the canonical element IDs, and report which additional
governance and capability evidence is required before candidate feature continuation.
