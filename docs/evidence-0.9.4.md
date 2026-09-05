# Program Kit 0.9.4 release evidence

The web boundary is now expressed through dedicated `IWebShellFeature` and `IMiddlewareFeature`
packages. Profile selection supplies the managed baseline; consumer `shells.json` supplies explicit
overrides. The canonical composition is used by both runnable-host staging and OpenAPI export, so
authentication, middleware ordering, endpoint contributions, and optional Problem Details cannot
silently diverge between build-time and runtime views.

The .NET OpenAPI exporter recognizes the built-in packaged features from their NuGet identities,
validates their dependencies and route contributors, and composes only the OpenAPI contributor into
the export application. Export first validates the managed toolchain in read-only mode, uses the
official `oasdiff` command shape with a legacy version-probe fallback, and runs with repository-local
NuGet packages, HTTP cache, scratch, plugin cache, CLI home, and Windows profile directories.

Runtime staging writes schema-defined, atomic evidence over every staged package identity, package
hash, configuration hash, and canonical closure digest. Failed or interrupted staging leaves an
explicit unsatisfied record. Runnable-host description and OpenAPI export recompute and require the
same-run closure, rejecting stale, modified, or differently targeted stages with `PKR022`.

Upgrade regression coverage proves that an unavailable Specify CLI stops before the mutation lock
and leaves the repository byte-identical. Stale Program Kit package locks produce `PKU113` plus
machine-readable renewal evidence containing exact force-evaluate and locked restore commands; the
updater does not perform an implicit network restore. Managed build and OpenAPI execution are also
covered against hostile ambient NuGet configuration.

Authorization ownership regressions reject role/provider-claim parsing and canonical permission
parsing in application projects while permitting endpoint policy attachment and resource/state
rules. Local persona passwords occur only in the explicitly marked non-production Keycloak realm;
browser tests load them through one fixture module without logging or retaining trace, video, or
screenshot artifacts. Both BFF-cookie and SPA-PKCE realms successfully import into the digest-pinned
Keycloak image and use the supported `post.logout.redirect.uris` client attribute.

Publication workflows verify public NuGet availability and attach an immutable host-image evidence
document containing the release tag, source commit, runtime version, repository, tag, digest, and
digest-qualified reference.
