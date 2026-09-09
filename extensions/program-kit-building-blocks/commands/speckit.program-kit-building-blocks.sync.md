---
description: Plan, check, or apply an Accepted deterministic building-block selection.
scripts:
  py: scripts/building_blocks.py
---

# Program Kit building-block synchronization

Use `draft` to create `docs/architecture/building-block-selection.json` from capability suggestions
without accepting any decision. Complete its explicit scopes, targets, instances, bindings, and
options. Use `accept` only after the cited decisions already exist as Accepted in
`docs/architecture/architecture-map.json`; it binds and registers the exact canonical selection.

The normal workflow is non-interactive and fail closed:

1. Run `draft --capability <id>` or `catalog-hash` while preparing the Draft.
2. Run `accept --decision-id <accepted-id> --rationale <text>` after completing the Draft.
3. Run `plan`; review the ordered lock and all managed-output ownership records.
4. Run `apply` with the exact reviewed `planDigest`.
5. Run `restore_dependencies.py renew --approved`, then `locked --approved`; both are explicit
   networked operations and preserve separate native-lock evidence. When a credential-owning
   supervisor is present, use the read-only `request-renew` and `request-locked` modes instead; the
   supervisor must recompute each request before performing the corresponding approved restore.
6. Run `public_availability.py` against the selected lock; publication additionally uses `--all`.

`plan` and `check` are read-only. `apply` never supplies an architectural default and refuses a
changed plan digest. It preserves consumer-owned entries, rejects unregistered catalog package
references, and uses a recoverable transaction. If an interrupted journal exists, run `recover`
before planning another write. Registry credentials, configuration secrets, and deployment values
never belong in the selection, generated lock, command arguments, or logs.

Direct functional dependencies remain visible in their owning project or package manifest. The
generated building-block lock records exact versions, sources, target assignments, feature
activation, configuration requirements, and provenance; native package locks continue to own
transitive resolution.
