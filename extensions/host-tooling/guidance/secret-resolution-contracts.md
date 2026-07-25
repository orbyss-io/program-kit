# Typed secret resolution contracts

`Orbyss.ProgramKit.SecretResolution` defines the provider-neutral boundary
approved by `PKHT-W025`. It does not provide a secret store, broker, universal
resolver, configuration control plane, or provider product integration.

## Canonical input

A `SecretReferenceDescriptor` contains:

- a stable non-secret identity;
- an explicit disclosure classification;
- one finite expected result kind;
- an exact resolver-capability revision;
- an exact adapter-owned locator-artifact revision and its classification.

The locator artifact and its payload belong to the selected provider adapter.
Program Kit does not invent an interpolation string or copy the locator payload
into generated source, logs, diagnostics, or evidence.

## Runtime results

Resolvers may expose only the finite typed capabilities in
`SecretResultKind`: configuration text or bytes, certificate, opaque mounted
file handle, opaque credential handle, assertion service, or a workload
identity capability with no secret material. The base runtime lease never
exposes `object` or `string` as a universal credential transport.

`IConfiguration` and Options may consume configuration text or bytes. Other
capabilities remain native typed runtime objects and are not coerced into
configuration.

## Change and reaction boundary

`SecretChangeSignal` contains only stable reference identity, safe generation,
status, observation, expiry, and change-kind metadata. It cannot carry resolved
material, provider messages, locator values, paths, tenant identifiers, or
certificate identifiers.

Each consumption binding explicitly selects hot replacement, client
recreation, reconnect, resource recycle, host restart request, manual handling,
or unsupported rotation. The .NET compiler generates a disposable hosted
subscription with a finite channel. The callback only validates and queues
metadata. A consumer-owned reaction service performs the selected behavior.

A queue rejection, invalid signal, consumer exception, mismatched result, or
false success becomes a stable material-free failure result. The generated
subscription reports success only after the consumer returns a matching valid
successful reaction result. Manual and unsupported reactions cannot report
automatic success.

These mechanics do not claim atomic rotation, zero downtime, rollback,
cross-process consistency, last-known-good behavior, or successful provider
change as successful application reconfiguration.
