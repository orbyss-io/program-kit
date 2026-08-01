# Snapshot source navigation

The workspace snapshot is an orientation projection, not semantic authority.
To inspect custom behavior, follow the artifact entry whose `ownership` is
`seeded-handoff`, verify its digest against the referenced workspace-relative
file, and then inspect that consumer-owned source. Follow `rootBundle`,
`provenance`, `evidence`, and `receipts` the same way. Never infer behavior from
artifact names, generated host code, or the snapshot alone.
