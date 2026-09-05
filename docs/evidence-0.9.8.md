# Program Kit 0.9.8 correction evidence

The release candidate adds deterministic destination-boundary and recovery coverage to the complete
Program Kit release suite:

- `validate_local_upgrade.py` marks an existing Program Kit Codex `SKILL.md` read-only, runs the
  updater, and requires `PKU115` before the bundle step. File-content hashes before and after the
  probe must be identical, the blocked path must be reported, and the outside-sandbox retry route
  must be present.
- The same test uses a controlled Spec Kit proxy that permits the bundle and workflow steps, then
  fails the governance-extension step. It asserts the deliberately mixed intermediate state and
  requires an ordinary rerun to converge every manifest, registry, managed baseline, and governed
  version record to the release version.
- `validate_components.py` requires the stable diagnostic and release-owned updater contract.
- Release-profile discovery reads both the consumer's current managed file map and the selected
  profile manifests from the candidate release, covering additions, replacements, and retirements.
- `validate_web_security_assurance.py` exercises effective-name network intersection, an implicit
  default-network disconnection with exact consumer-overlay remediation, a renamed network key, and
  stale live-container attachments.
- `validate_keycloak_realm_import.py` creates unique disposable containers with no database volume
  for both profiles, rejects ignored-scope import warnings, submits each profile's real managed PAR
  request, follows the cookie-bearing authorization redirects, and requires the Keycloak login form.

The research finding was that Spec Kit extension and preset registration targets every detected
integration command directory, and an existing command may be unlinked before it is rewritten.
Spec Kit records installed integration-owned files under `.specify/integrations/*.manifest.json` and
extension/preset agent registrations in their local registries. Those records provide the generic,
integration-neutral destination authority used by the new preflight.

The topology finding was that Compose validates each file set structurally but does not infer that a
consumer service's internal origin and `depends_on` require a shared effective network. The managed
launcher is the only point that knows the selected consumer overlay and the live project, so it owns
desired-model validation and post-start container reconciliation; the updater does not rewrite a
consumer-owned Compose file.

The identity smoke previously used fresh containers correctly, but stopped after readiness and
discovery metadata. It therefore never exercised the imported clients or their requested scopes.
The new PAR/login entry checks make a missing client scope fail with Keycloak's real protocol error.
