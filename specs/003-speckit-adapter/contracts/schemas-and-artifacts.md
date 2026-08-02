# Schema and Artifact Contract Catalog

All schemas use JSON Schema 2020-12, closed object properties, exact schema
identities, and `program-kit.canonical-json/v1` machine bytes. Restricted YAML
is an authoring projection only where listed.

## Program Kit schemas

| Schema identity | Authoring | Owner | Purpose |
|---|---|---|---|
| `program-kit.distribution-binding/v1` | JSON | Program Kit | Exact invoked CLI/package/runtime identity |
| `program-kit.workspace-init-request/v1` | JSON | Consumer | Explicit neutral bootstrap request |
| `program-kit.workspace/v1` | Restricted YAML | Seeded then consumer | Requested exact composition and optional default |
| `program-kit.catalog-request/v1` | JSON | Consumer | Exact local distribution inventory request |
| `program-kit.distribution-catalog/v1` | JSON | Program Kit | Read-only installed capability inventory |
| `program-kit.workspace-restore-request/v1` | JSON | Consumer | Exact manifest-to-lock resolution request |
| `program-kit.workspace-lock/v1` | JSON | Program Kit generated | Accepted distribution/contract/provider closure |
| `program-kit.preparation-request/v1` | JSON | Adapter generated | Effect-free prospective construction request |
| `program-kit.preparation-proposal/v1` | JSON | Program Kit generated | Authorizable ungranted proposal and live preconditions |
| `program-kit.authority-decision-record/v1` | JSON | Consumer/human | Separate exact human decision declaration |
| `program-kit.authority-record-request/v1` | JSON | Consumer/agent | Request to configured repository authority provider |
| `program-kit.operation-result/v2` | JSON | Program Kit | Single current structured result for every public command |

Existing `program-kit.factory-request/v1`, `program-kit.authority-grant/v1`, software
bundle, resolution, receipt, snapshot, and common schemas are referenced without
modification.

## Adapter schemas

| Schema identity | Authoring | Owner | Purpose |
|---|---|---|---|
| `program-kit.spec-kit-adapter-config/v1` | Restricted YAML | Consumer | Repository activation/default policy and Program Kit paths |
| `program-kit.spec-kit-handoff/v1` | Restricted YAML | Seeded then consumer | Reviewed factory projection |
| `program-kit.spec-kit-handoff-review/v1` | JSON | Consumer/human | Exact named review evidence |
| `program-kit.spec-kit-adapter-request/v1` | JSON | Consumer/agent | One discriminated adapter executable request |
| `program-kit.spec-kit-adapter-compatibility/v1` | JSON | Adapter release | Exact supported release/contract matrix |
| `program-kit.spec-kit-adapter-manifest/v1` | JSON | Adapter generated | Input/output/ownership/invalidation bindings |
| `program-kit.spec-kit-adapter-result/v1` | JSON | Adapter | Structured adapter operation result |
| `program-kit.spec-kit-adapter-diagnostic-catalog/v1` | JSON | Adapter release | Exact adapter diagnostic definitions |

## Workspace paths and ownership

```text
.config/dotnet-tools.json                         .NET-owned
program-kit.yaml                                 seeded -> consumer-owned
program-kit.lock.json                            Program Kit generated-owned
.program-kit/state/**                            Program Kit generated-owned
.program-kit/authority/**                        seeded handoff / provider records
.specify/extensions.yml                          Spec Kit-owned
.specify/extensions/orbyss-program-kit-adapter/** Spec Kit extension-owned
.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.template.yml extension-owned
.specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml consumer-owned
specs/<feature>/program-kit/handoff.yaml          seeded -> consumer-owned
specs/<feature>/program-kit/handoff-review.json   consumer-owned
specs/<feature>/program-kit/generated/**          adapter-generated-owned
consumer source/implementation                    consumer-owned
generated product/receipts/evidence               Program Kit ownership rules
```

No artifact combines generated and editable regions. Each manager modifies only
its owned installation/state files. A seeded handoff is created only when absent
and is never later overwritten by its creator. The exact project-config file is
the one consumer-owned exception inside the Spec Kit installation directory;
disable/update never rewrites it and removal uses Spec Kit `--keep-config`.
`orbyss-program-kit-adapter-config.local.yml` and environment overrides are not
semantic inputs and are reported rather than merged.

## Conditional feature artifact set

```text
specs/<feature>/program-kit/
├── handoff.yaml
├── handoff-review.json
└── generated/
    ├── adapter-manifest.json
    ├── definitions/
    │   ├── software-bundle.json
    │   └── dotnet-component-api.json
    ├── requests/
    │   ├── prepare.json
    │   ├── explain.json
    │   ├── construct.json
    │   └── evaluate.json
    └── results/
        ├── prepare.json
        ├── explain.json
        ├── construct.json
        └── evaluate.json
```

Later files exist only after their prerequisites. A disabled/non-factory feature
creates no `program-kit/` directory. Disablement never deletes an earlier set.

## Publication rules

1. Resolve all logical paths under the declared workspace without following a
   reparse-point escape.
2. Reject duplicates under ordinal and platform case-collision comparison.
3. Stage a complete immutable output set outside live destinations.
4. Validate every schema, canonical byte profile, ownership declaration,
   referenced input, and expected live-path state.
5. Refuse overwrite of consumer-owned, Program Kit-owned, drifted, or unknown
   bytes.
6. Atomically publish the complete set; interrupted state remains untrusted and
   recoverable.
7. Record exact output digests and invalidation sets in the adapter manifest.

## Cleanup rules

Cleanup is a separate explicit adapter operation. It may remove only an
adapter-generated candidate whose current bytes match the exact digest in the
current adapter manifest and whose schema marks it regenerable. It never removes
handoffs, reviews, Program Kit requests/results retained as evidence, product
files, locks, receipts, snapshots, consumer source, or other managers' files.
