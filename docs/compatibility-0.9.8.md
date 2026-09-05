# Program Kit 0.9.8 compatibility report

0.9.8 is a compatible updater-safety correction over 0.9.7. Program Kit components advance to
`0.9.8`; runtime packages and the host image remain `0.9.7-preview.1` because no runtime source or
package contract changed.

The offline updater now treats destination mutation capability as part of the same preflight
boundary as Spec Kit launcher execution. Before acquiring the component-mutation lock or invoking
the first Spec Kit install command, it validates the component registries, every installed or
previously registered integration command root, current and release-desired managed-profile paths,
governance state, NuGet renewal evidence, and every planned OpenAPI reconciliation target.

Integration paths come from Spec Kit's repository-local integration manifests; Program Kit does not
encode `.agents`, `.claude`, or another agent-specific layout. Existing Program Kit command files
under those roots are checked explicitly, while directory probes verify create, write, rename, and
delete capability and remove their sentinels immediately.

A denied destination stops with `PKU115`, names the exact path and purpose, confirms that no
component mutation started, and prints the updater invocation for a user-owned PowerShell outside
the sandbox. Elevation is only needed when the operating-system ACL—not the sandbox—is the cause.

The updater remains sequential and intentionally does not claim transactionality across independent
Spec Kit processes. If an unrelated process failure interrupts an older or current run after an
early component step, rerunning the same updater is the supported recovery: every install primitive
is replace/converge-safe, and final installation validation remains authoritative.

Authenticated profile startup now validates the fully merged identity, application, and selected
consumer-overlay Compose models before starting a service. A service-level `depends_on` or internal
URL reference must resolve to a target service on at least one network with the same effective
Compose network name. This covers renamed network keys as well as added and removed networks without
requiring Program Kit to own the consumer overlay. `PKC001` reports the overlay, disconnected
services, dependency source, and target network. Full startup force-recreates application-side
services, then `PKC002` compares every running container attachment with the desired model so a
container retained from an older topology cannot silently survive.

The managed Keycloak realm now explicitly defines every scope referenced by the BFF and SPA clients:
`basic`, `profile`, `roles`, `web-origins`, `acr`, `offline_access`, and `program-kit-api`.
Repository synchronization validates that referenced and requested scope names are materialized;
consumers must not edit or suppress scopes in the managed realm.
