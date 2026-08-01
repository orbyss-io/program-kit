# Diagnostic Contract: Initial v1 Catalog

## Catalog identities

- Kernel catalog: `orbyss.program-kit:diagnostic-catalog:kernel@1.0.0`
- .NET provider catalog:
  `orbyss.program-kit.dotnet:diagnostic-catalog:provider@1.0.0`
- Both are canonical `program-kit.diagnostic-catalog/v1` artifacts with exact
  SHA-256 digests recorded in the distribution manifest and operation lock.

An ID's trigger and violated-invariant meaning are permanent. Wording may change
only under a new exact catalog revision. Material trigger, invariant, category,
subject, or consequence changes require a new ID.

## Kernel entries

| ID | Category | Default severity | Permanent trigger/invariant | Primary disposition |
|---|---|---|---|---|
| `program-kit.kernel/PKREQ0001` | request | error | A required command or request input is absent; no input is guessed | provide-input |
| `program-kit.kernel/PKREQ0002` | request | error | Input cannot be parsed or structurally validated under its exact declared profile | revise |
| `program-kit.kernel/PKREQ0003` | request | error | Command, operation, option, or continuation binding conflicts with another supplied value | revise |
| `program-kit.kernel/PKSEM0001` | semantic | error | The same governed identity/revision resolves to conflicting canonical content | revise |
| `program-kit.kernel/PKSEM0002` | semantic | error | Required meaning is incomplete, unsupported, or cannot be represented without undisclosed loss | revise |
| `program-kit.kernel/PKRES0001` | resolution | error | No exact selected provider/profile/contract/content is available | provide-input |
| `program-kit.kernel/PKRES0002` | resolution | error | More than one candidate remains where one exact selection is required | provide-input |
| `program-kit.kernel/PKRES0003` | resolution | error | Exact relationship evaluation proves the selected endpoints incompatible | revise |
| `program-kit.kernel/PKPOL0001` | policy | error | No current exact authority grant permits the requested subject/operation/effect | request-approval |
| `program-kit.kernel/PKPOL0002` | policy | error | A waiver is invalid, expired, revoked, overbroad, or targets a non-waivable gate | stop |
| `program-kit.kernel/PKCON0001` | conformance | error | A mandatory applicable gate failed or was not evaluated | revise |
| `program-kit.kernel/PKCON0002` | conformance | error | Equal claimed construction identities produced different claimed canonical bytes | stop |
| `program-kit.kernel/PKWSP0001` | workspace | error | A generated-owned live artifact differs from the exact admitted digest | repair |
| `program-kit.kernel/PKWSP0002` | workspace | error | A planned write collides with incompatible ownership, path identity, or live-state preconditions | repair |
| `program-kit.kernel/PKWSP0003` | workspace | error | Publication began but complete trusted live state cannot be proven | repair |
| `program-kit.kernel/PKWSP0004` | workspace | error | A workspace snapshot's closure/evidence bindings no longer describe current evaluated state | retry |
| `program-kit.kernel/PKEXT0001` | external | error | An exact external tool returned a non-success or invalid structured observation | retry |
| `program-kit.kernel/PKEXT0002` | external | error | Required exact bytes, source, package, tool, or evidence are unavailable | stop |
| `program-kit.kernel/PKINT0001` | internal | fatal | A recoverable command-path failure prevented the normal result pipeline from completing | stop |

`PKINT0001` is embedded with the minimal fallback serializer and disclosure
filter. It cannot depend on normal catalogs, providers, schema evaluation, or
rendering.

## .NET provider entries

| ID | Category | Default severity | Permanent trigger/invariant | Primary disposition |
|---|---|---|---|---|
| `program-kit.provider.dotnet/PKDOT0001` | conformance | error | Two endpoint contributions resolve to the same route identity when the seam forbids duplicates | revise |
| `program-kit.provider.dotnet/PKDOT0002` | conformance | error | A contribution has no exact selected owning host assembler | provide-input |
| `program-kit.provider.dotnet/PKDOT0003` | conformance | error | Meaningful endpoint order remains ambiguous after exact resolution | provide-input |
| `program-kit.provider.dotnet/PKDOT0004` | conformance | error | Generated source or activation does not compile/conform against exact CShells 0.0.28 | stop |
| `program-kit.provider.dotnet/PKDOT0005` | resolution | error | Local package identity, exact version, NuGet content hash, Program Kit digest, or lock disagree | stop |
| `program-kit.provider.dotnet/PKDOT0006` | external | error | Locked local restore/build/test/pack returned a non-success or unverifiable observation | retry |
| `program-kit.provider.dotnet/PKDOT0007` | conformance | error | Generated consumer dependency evidence contains a forbidden or unapproved runtime dependency | stop |

## Deterministic ordering and grouping

The complete collection is ordered by:

1. protocol phase rank;
2. category rank in the constitutional category order;
3. severity rank `fatal`, `error`, `warning`, `info`;
4. diagnostic ID ordinal;
5. occurrence key ordinal.

Exact duplicates group only when ID, typed subjects, rule, safe parameters, and
typed cause are canonically equal. `occurrenceKey` is SHA-256 over that canonical
tuple; occurrence count preserves multiplicity. Distinct subjects, rules,
observations, or causes remain distinct.

## Disclosure floor

- Catalog parameter schemas declare `public`, `repository-relative`, or
  `withheld`.
- Secret values, secret-derived digests, protected absolute paths, unsafe
  command lines, raw external output, exceptions, and stack traces are always
  withheld.
- Withholding emits a structured reason and policy reference, never a reversible
  placeholder or fingerprint.
- JSON, text, verbose, progress, and fallback paths share the same floor.
- External output becomes evidence only after a declared adapter and disclosure
  policy; it never enters a diagnostic verbatim.

## Remediation contract

Every remediation names exact targets, preconditions, effect class, required
authority, postconditions, safe retry phase, and either an existing structured
request artifact or an inline factory request, argument array, or digested
patch. An inline request is returned in the result for the caller to materialize
and submit under separate authority. Remediation is a proposal, not a grant.

Reference expectations:

- missing exact selection:
  `program-kit.kernel/PKRES0001`, `needs-input`, `none`, `provide-input`;
- duplicate route:
  `program-kit.provider.dotnet/PKDOT0001`, `blocked`, `none`, `revise`;
- generated drift:
  `program-kit.kernel/PKWSP0001`, `blocked`, `none`, `repair`;
- interrupted publication:
  `program-kit.kernel/PKWSP0003`, `blocked` or `faulted`,
  `indeterminate`, `repair`;
- normal pipeline failure:
  `program-kit.kernel/PKINT0001`, `faulted`, safest proven effect, `stop`.
