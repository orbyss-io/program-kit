# Implementation Plan v2 to v3 migration

Planning `3.0.0` adds explicit static-conformance execution structure without
changing the existing implementation-plan execution authority.

Migration requires the human or an already approved design projection to supply:

- the exact `StaticConformanceDisposition@1.0.0` reference and matching plan
  state;
- exact gate-design and planned gate-definition, selection-lock, and
  activation-evidence identities when applicable; and
- one exact `gate-establishment`, `product`, or `closure` classification plus
  activation-matrix and verification-profile references for every v2 work-unit
  ID.

The migration rejects missing, duplicate, and extra classifications. It does
not derive a role from sequence, file paths, allowed edits, names, or repository
contents.

Planning v3 validates explicit dependency paths:

- every product and closure unit follows all gate-establishment units;
- closure follows every product unit;
- create-new and extend-existing expose only dependency-ready
  gate-establishment work until compatible activation evidence exists;
- reuse-existing admits no work without a compatible materialized selection
  lock and activation evidence;
- accepted-empty admits ungated dependency-ready work only through its exact
  accepted disposition; and
- blocked-unavailable admits no work.

Admission is pure classification for the existing executor. It performs no
mutation, execution, or authority grant.
