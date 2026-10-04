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

New projects use the qualified default in `references/dependency-profiles/index.json` for both
engineering tools and the Draft selection. `draft --profile <id>` selects another qualified
combination. Draft pins are captured independently of the Program Kit version and remain suggestions
until the architecture decisions are Accepted. The profile's excluded activations remain blocked
during validation and acceptance. Changing the bundled template pins does not change this default;
register the exact qualified combination before changing the registry default. An explicit
`--catalog` is a custom qualification input and does not establish supported-combination evidence.

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

A Program Kit upgrade retains the consumer's accepted exact dependency profile under
`.program-kit/dependency-profile.json`; it does not advance Foundation, Forms, Localization,
analyzers, exporter, or host-image pins merely because the Program Kit bundle changed.
Treat a dependency change as its own reviewed transition:

1. Run `dependency_profiles.py list` for combinations with preserved qualification evidence.
2. Run `dependency_profiles.py draft --profile <id> --target .`. Review the proposed selection,
   exact changed artifacts, original-input archive, profile digest, and any producer-contract,
   planning or readiness changes in the returned packet. Those exact original and proposed files
   are sealed into the same review digest; a stale producer pin outside the original profile fails.
3. Record an Accepted architecture decision containing the exact profile SHA-256 and transition
   `reviewSha256`. The review binds the preserved originals and intended changes as well as the pins.
4. Run `dependency_profiles.py accept --transition <repository-relative-path> --decision-id <id>
   --rationale <reviewed-rationale>`. This consumes existing authority and preserves selection history.
5. Synchronize engineering pins through maintained `dotnet_sync.py`, renew affected compatibility
   proofs through their existing lifecycle, then review and apply the
   building-block plan and renew native locks. Acceptance alone is not consumer readiness.

Unlisted combinations require qualification before registration as supported. The historical
v0.12.5 profile records its published Release coverage; its exporter has the documented Assurance
limitation. A private corrected-exporter candidate is not public availability evidence.
The historical exporter-only upgrade option remains a bounded compatibility bridge. New dependency
changes use this reviewed profile transition, including producer reconciliation. A qualified earlier
profile may be selected through its explicit review; the historical bridge still permits only its
reviewed forward exporter change. Interrupted promotions resume sealed originals/proposals, and
repeating completed acceptance preserves later analysis and proof history.
