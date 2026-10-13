# Typed executable Foundation composition

The sole authoring input is schema version 2 of `eng/foundation-composition.json`.
Start from `templates/dotnet/compositions/application-foundation.json` or its
`application-foundation-postgresql.json` variant, then populate the consumer's Accepted
owners, feature paths, assigned endpoints/clients and database bindings. The retained
`foundation-bff-keycloak*.json` files are version 1 migration fixtures and are rejected
by normal generation/execution.
Define stable typed resources (features, shells, hosts, database servers/databases,
identity authorities/clients/protected resources, frontends), explicit bindings and
environment placement. Link them to the consumer's Accepted architecture and
selection identities. Resource counts come from this graph: multiple contexts can
bind separate databases on a shared server, and multiple applications can use one
authority with separate registrations and audiences. This supplies no aggregate C#
project or consumer host. Feature and context sources are consumer-owned after scaffold.

A frontend can bind several distinct page routes in the same shell while sharing one
compiled deployment root. Each `frontend` binding supplies its `routeId` and `path`,
with optional `pagePermission` and `bootstrapPermission`. Both admissions remain
authenticated and private; bootstrap permission adds to page admission. These fields
preserve existing route restrictions during migration and never grant permissions to
users. Product role/permission assignments remain consumer-owned.

`eng/composition_run.py prepare` verifies prerequisites, acquires exact dependencies
and browser executables, builds frontends, stages admitted assets/packages and provisions
owned databases and identity registrations. Existing identity users and registration IDs are
preserved; removed owned clients are disabled. `run` starts the generated Docker Compose and checks real activation,
provider connectivity, BFF authentication/theme and page runtime loading. `update --host
<resource-id>` rebuilds affected native compilation dependants and preserves unrelated
services; `stop` preserves owned database/identity volumes. Implementation's single
prehook calls the same prepared run/readiness route. First acquisition is explicit.

Preparation validates the planned architecture, then actually builds, packages and
starts the selected foundation. Accepted product bindings may still name interfaces
and implementations that have not been written. Keep those bindings in the plan;
the full evaluated/compiled product architecture check remains an implementation
verification obligation. Foundation readiness does not claim that check has passed.

Generated settings, realm imports and Compose files are outputs. Legacy finite
inputs require explicit `eng/composition_migrate.py` preview/apply, followed by normal
managed reconciliation and fresh implementation entry. Preserve task IDs, valid owned
code, baseline, effort, original locks and Accepted decision history. Reconcile active
scoped decisions, affected plans and retired placements; no repeated bootstrap/intake.
For an existing consumer with no finite legacy input, supply `composition_migrate.py --proposal
<local-reviewed-v2.json>`; preview binds the Accepted authority, current plans/tasks and locks.
Apply its exact plan digest, then use the same managed synchronization and preparation route.
The proposal is an import document; the active definition remains the one canonical model.

The initial executable adapter qualifies PostgreSQL, managed Keycloak and BFF hosts.
External authority/database placement is represented separately from owned provisioning;
an unqualified provider/profile/handshake reports its missing capability before execution.
Application-only/delegated intent never silently chooses another protocol or grant.
Local insecure BFF applications require distinct browser hostnames because ports do
not isolate the pinned publisher's cookies. HTTP/TLS routing/certificate capabilities
must be qualified for the actual environment. Private imports/personas are synthetic
Development inputs, not production authority provisioning.
