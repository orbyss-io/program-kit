# Program Kit 0.8.11 profile-transition and browser-contract audit

> Architecture amendment: the durable implementation also removes the host-owned
> `ProgramKitWebBoundary`. Each authentication profile is linked to a dedicated CShells feature
> NuGet package; default headers, OpenAPI, and Problem Details are separate, replaceable feature
> packages. No web/auth policy remains in `ProgramKit.Host`.

Date: 2026-09-05

## Scope and conclusion

The reported `spa-pkce` to `bff-cookie` residue is one instance of a general desired-state
reconciliation gap. Program Kit 0.8.11 records the active selection and per-file hashes, but it does
not retain the selected manifest graph, migration lineage, tombstones, structured-field migrations,
or a recoverable transaction. A write evaluates and mutates one path at a time before it knows that
the complete plan is conflict-free. Therefore a failed or successful transition can leave a hybrid
tree.

The BFF fixture also has two independent runtime-contract defects: both alternative Keycloak clients
remain enabled, and logout is asserted only through Playwright's HTTP client even though its
header-bearing cross-origin redirect shape is not consumable as a browser navigation.

The durable fix should be a versioned reconciliation engine and manifest/state schema, not a growing
list of ad-hoc deletions. The browser contract should remain same-origin and use a CSRF-protected
top-level form POST (or an equally browser-native continuation), with page-context evidence and an
explicit machine-readable route/response contract.

## Current transition inventory

### Web profile dimension

The supported selections are `none`, `bff-cookie`, and `spa-pkce`. `none` has no profile manifest;
the other two overlay `templates/dotnet/managed-files.json` with a profile manifest. All six
pairwise switches are accepted by the CLI, but they do not all work:

| Transition | 0.8.11 result | Confirmed consequence |
| --- | --- | --- |
| `none -> bff-cookie` | exit 2 | `hostsettings.json` ownership conflict occurs after new BFF files are created; state remains `none`, so the tree is hybrid and the new files are untracked by state. |
| `none -> spa-pkce` | exit 0 | Completes because the target `hostsettings.json` becomes managed. |
| `bff-cookie -> none` | exit 2 | `hostsettings.json` ownership conflict; BFF state and files remain. |
| `bff-cookie -> spa-pkce` | exit 0 | File graph converges because BFF paths are a subset of SPA paths, but both alternative Keycloak clients remain enabled. |
| `spa-pkce -> bff-cookie` | exit 0 | Eight former SPA files remain on disk but disappear from state. The stale verifier is then activated by file existence. |
| `spa-pkce -> none` | exit 0 | Twenty-four former profile files remain on disk but disappear from state. |

The reproduced eight-file SPA residue is:

- `.program-kit/spa-pkce.json`
- `.program-kit/spa-pkce.schema.json`
- `eng/program-kit/verify_spa_profile.py`
- `eng/program-kit/web/spa-security.json`
- `eng/program-kit/web/spa-session.ts`
- `eng/program-kit/web/tests/spa-session.spec.ts`
- `eng/program-kit/web/verify_spa_security.py`
- `eng/program-kit/web/vite.security.mjs`

`Dev.ps1` and `Test-Web.ps1` run `verify_spa_profile.py` when the path exists rather than when the
authoritative active profile is `spa-pkce-v1`. This is the only current profile-by-file-presence
activation found in the managed .NET scripts. It turns otherwise inert residue into `PKW107`.

### Persistence dimension

The CLI records `none`, `ef-postgresql`, `ef-sqlserver`, or `ef-sqlite`, but all three provider props
files are installed for every selection. The selected provider is actually activated by a
consumer-owned import in an owning provider project. Pairwise sync changes only
`managed.json.persistenceProfile`; the sync does not validate that consumer imports agree. This
avoids automatic deletion risk today, but means the recorded selection is not a complete desired
state and cannot prove provider coherence.

### Bundle and optional-feature dimensions

There is one Program Kit bundle with mandatory workflow, governance extension, .NET extension, and
preset contributions. The .NET baseline sync itself is optional; there are no independently
removable per-file optional bundles in `dotnet_sync.py`. Spec Kit owns extension/preset/workflow file
lifecycle outside `.program-kit/managed.json`. Future optional template groups would encounter the
same residue problem because the current engine has no selection graph or retired-contribution
reconciliation.

### Runtime fixture selection

Both fresh BFF and fresh SPA output contain enabled `program-kit-bff` and `program-kit-spa` clients.
The SPA realm renderer customizes its client but never removes the BFF client; BFF copies the common
two-client realm unchanged. This contradicts the one-selected-profile invariant and expands the
local fixture's enabled attack surface.

## Ownership and migration evidence in 0.8.11

`.program-kit/managed.json` schema 1 records:

- the Program Kit version;
- web and persistence selection strings;
- per-path `ownership`, `templateHash`, and `installedHash`.

That is enough to update an unchanged managed file and detect ordinary managed-file drift. It is
not enough to reconcile arbitrary transitions safely:

- it does not record which base/profile/optional contribution owned a path;
- successful profile switches discard former path records, so later repair cannot authenticate
  stale files against their prior installed bytes;
- it does not distinguish the original scaffold baseline from a later observed consumer edit;
- `configuration` files are accepted wholesale and their current hash becomes `installedHash`, so
  that field cannot be used as deletion authority;
- removals rely on the current base manifest's unversioned `obsoleteFiles` list; profile manifests
  have no tombstones, moves, or migrations;
- structured JSON/YAML fields have no field ownership or schema migration record;
- source, generated, derived, configuration, and evidence files share essentially the same lifecycle;
- skipped upgrades work only when every historical tombstone remains forever in the latest manifest;
- rollback and interrupted-migration evidence do not exist.

Ownership transitions are asymmetric. An unchanged managed file may become scaffold-owned and an
unchanged scaffold may become managed, while a modified scaffold conflicts. `NuGet.config` has a
single bespoke semantic migration. No general mechanism expresses these rules or previews the
ownership transfer.

## Atomicity and preview evidence

`--check` is read-only and reports counts for create, update, conflict, and removal. It does not
report contribution provenance, ownership transitions, structured migrations, preserved files, or
postconditions. Write mode does not first require that same complete plan to be conflict-free.
Instead it writes active files, then removes obsolete files, then returns 2 if any conflict exists;
state is written only on success. The reproduced `none -> bff-cookie` case therefore created BFF
files before the later `hostsettings.json` conflict and left state claiming `none`.

There is no transaction journal, staging tree, backup set, commit marker, resume, or rollback. The
upgrade-level lock prevents concurrent Program Kit mutations but does not make the sequence atomic.

## Browser logout mechanics

The current BFF contract obtains a token via `GET /bff/antiforgery`, requires the custom
`X-CSRF-TOKEN` header on `POST /bff/logout`, and has the host return a cross-origin 302 to the OIDC
provider. The managed Playwright test uses `BrowserContext.request`, not code executing in the page.

A disposable two-origin browser test measured the actual page behavior:

- `fetch('/logout', { headers: {'X-CSRF-TOKEN': ...}, redirect: 'manual' })` returned an
  `opaqueredirect` response with status 0, no readable `Location`, and no usable destination URL;
- the same header-bearing fetch with `redirect: 'follow'` failed when the provider response did not
  grant CORS;
- a cross-site subresource fetch with credentials did not send the provider's `SameSite=Lax`
  session cookie;
- a top-level same-origin form POST containing a CSRF form field followed the 302 as navigation and
  the provider received its `SameSite=Lax` cookie.

These results follow the [WHATWG Fetch redirect contract](https://fetch.spec.whatwg.org/), where
manual redirects outside navigation expose an opaque-redirect filtered response; the
[HTML form submission contract](https://html.spec.whatwg.org/dev/form-control-infrastructure.html),
which offers action/method/enctype/target but no arbitrary request-header facility; and
[OpenID Connect RP-Initiated Logout](https://openid.net/specs/openid-connect-rpinitiated-1_0.html),
which requires redirecting the end-user's user agent to the provider logout endpoint. Microsoft
documents that ASP.NET Core antiforgery accepts the request token in a
[form field or request header](https://learn.microsoft.com/aspnet/core/security/anti-request-forgery?view=aspnetcore-10.0).
The current HTTP-client-only assertion therefore misses a real SPA integration failure.

The BFF `web-contract.json` also omits the signed-out and access-denied routes, OIDC callback route
semantics, exact user/antiforgery/logout response shapes, and browser-observable recovery behavior.

## Proposed durable reconciliation design

### Desired-state manifests and state schema 2

Build one complete desired-state graph before touching the consumer. Every contribution has a
stable ID, version, selection predicate, lifecycle class, source identity, target path, ownership,
and optional renderer/schema. The state stores the last successfully committed graph, not only the
currently desired paths.

Each file record should include:

- contribution ID and source profile/dimension;
- contribution and template schema version;
- lifecycle: `managed`, `scaffold`, `configuration`, `derived`, `evidence`, or `generated`;
- template/baseline hash, last Program-Kit-written hash, and renderer/input hashes where applicable;
- ownership-transfer history and the last committed target path;
- structured schema ID/version for files with field migrations.

Selections belong in a typed `selections` object. Web profile, persistence profile, and future
optional groups are independent dimensions. State also records the desired-manifest digest,
applied migration IDs, last committed plan digest, and any recovery transaction ID.

### Versioned migration catalog

Manifests reference immutable migrations with stable IDs and applicable version/profile edges.
Operations include retire, move, split, merge, ownership transfer, render-from-input, and explicit
structured-field migration. Each operation declares preconditions, expected old hashes/schema,
the new owner/path/schema, conflict behavior, and postconditions. Skipped upgrades apply the ordered
migration chain; tombstones are not silently dropped from later releases.

Whole-file hashes remain the authority for managed bytes. Scaffold/configuration retirement is safe
only when current bytes equal their original template/baseline hash, not a later observed hash.
Modified consumer content is preserved and is a planning conflict. A path adopted by another
profile is reconciled as an ownership/source transition, not removed and recreated. Structured
fields change only through named, versioned migrators with exact before/after schema validation.

### Plan, commit, and recovery protocol

1. Acquire the repository-scoped mutation lock and reject an unresolved prior transaction.
2. Load and validate state/schema, selections, current manifests, and the complete migration chain.
3. Read every affected path and build a deterministic plan containing creates, updates, moves,
   removals, ownership changes, structured migrations, preserved modifications, and conflicts.
4. Validate every renderer, source, schema, and global invariant. If any conflict exists, emit the
   plan and stop before the first consumer-file mutation.
5. `--check` emits the same plan in human and `--json` forms. A separate `--apply-plan <digest>` (or
   an internal equivalent in the release updater) prevents applying a plan different from the one
   reviewed.
6. Stage all new bytes and a recovery journal under `.program-kit/transactions/<id>`. Record backups
   for every replaced/removed path and fsync the journal before commit.
7. Apply atomic per-file replacements/removals, validate the final graph, then atomically replace
   `managed.json` last. On any error, restore backups. A later invocation must detect and either
   finish or roll back an interrupted journal deterministically.
8. Success requires no unmanaged residue for retired Program Kit contributions and exact agreement
   among `managed.json`, `.program-kit/web-profile.json`, `hostsettings.json`, the browser contract,
   realm fixture, and active scripts.

Launch/test scripts must branch only on the validated authoritative profile record and fail when
state/profile/configuration disagree. File existence may validate a required selected artifact; it
must never select a profile.

## BFF contract and fixture design recommendation

- Provision only `program-kit-bff` for BFF and only the configured public SPA client for SPA (the
  protected API audience client remains common). Profile transitions replace the realm as managed
  output and tests prove the unselected browser client is absent or disabled.
- Keep header-based antiforgery for `fetch`-driven unsafe API operations, and additionally expose the
  antiforgery form-field name/token for a browser-native logout form POST. The handler clears the
  local ticket first and returns the OIDC 302 in that top-level navigation. Missing/invalid/cross-site
  form tokens fail before mutation.
- Exercise logout from actual page code: obtain the token, construct/submit the same-origin form,
  observe provider navigation and the top-level return to the registered signed-out route, then
  prove `/bff/user` is anonymous. Retain separate provider-outage evidence for the application-
  controlled local-first terminal outcome described by ADR 0005.
- Expand and schema-version `web-contract.json` with managed versus feature-owned route namespaces,
  routes for login/user/antiforgery/logout/signed-out/access-denied and OIDC callbacks, exact
  methods/statuses/content types/schemas, error codes, redirect rules, and browser-observable session
  expiry/provider-failure behavior. Do not claim an error code the host does not emit.
- For BFF, the Program Kit host middleware owns same-origin browser response headers and WEB-V3
  should assert them on a real BFF response. `ViteConfig` is SPA-PKCE-only and must be rejected or
  hidden for BFF rather than invoking SPA-only verification.

## Required test matrix

- fresh `none`, BFF, and SPA installs;
- all six pairwise web switches, reverse switches, and a second idempotent sync;
- every persistence selection pair, plus agreement checks against consumer-owned provider imports;
- optional contribution add/remove once such a contribution exists;
- unchanged and modified managed, scaffold, and configuration paths during retirement/adoption;
- managed drift, ownership transfer, move/rename/split, structured schema migration, and generated/
  evidence lifecycle cases;
- direct and skipped-version upgrades through the same migration chain;
- conflict planning with zero mutation, injected interruption at every commit phase, automatic
  rollback/recovery, and reapplication;
- selected-profile-only runtime scripts and selected-client-only realm output;
- permission-probe `200`, `204`, non-2xx, and exact wrong-role `403` outcomes;
- real-page BFF login, form logout, provider return, missing/invalid/cross-site antiforgery, local-
  first provider failure, session expiry, access denied, and security-header evidence.

## Emergency correction and release recommendation

For already mixed 0.8.11 consumers, do not delete paths merely because they appear in the known SPA
list: successful 0.8.11 transitions discarded their prior state records. The safe repair must compare
each path against authenticated 0.8.11 source/rendered bytes (using the retained SPA configuration
where required), preserve mismatches as conflicts, and apply the cleanup through the transaction
planner. Until that exists, the consumer should remain blocked or perform an explicitly reviewed
manual migration.

The smallest emergency patch is selected-profile gating in `Dev.ps1`/`Test-Web.ps1`, the permission
probe `2xx` correction, and a versioned 0.8.11 SPA-residue migration with authenticated old-source
hashes. That can unblock validation without pretending the general problem is solved.

Because the durable reconciliation schema, migration protocol, fixture least-privilege change, and
browser-complete BFF contract materially change consumer tooling and managed contracts, the
recommended coherent release is Program Kit `0.9.0`, with a schema-versioned BFF contract/profile
revision if any externally observable v1 behavior changes. A narrowly scoped `0.8.12` should be used
only if the emergency patch is released separately and explicitly documented as not yet providing
general transition atomicity.
