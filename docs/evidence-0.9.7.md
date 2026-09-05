# Program Kit 0.9.7 correction evidence

The release candidate is covered by four deterministic regressions in addition to the complete
Program Kit release suite:

- `validate_local_upgrade.py` models the exact Windows uv launcher denial, validates the external
  environment, probes every Specify command through the release-owned bridge, and proves preflight
  leaves the consumer unchanged.
- `validate_analyzer.py`, `validate_dotnet_feature_host.py`, and `validate_openapi_exporter.py`
  exercise a dotted feature identity whose CLR type name cannot be safely derived. Build, runtime,
  and export now require the same explicit `[ShellFeature]` value.
- the managed `Test-Web.ps1` suite loads the realm fixture from its shipped directory before browser
  installation/execution; `validate_web_security_assurance.py` also proves that resolved path remains
  inside the consumer repository.
- `validate_keycloak_realm_import.py` starts the digest-pinned Keycloak image for both profiles and
  verifies public issuer/authorization/logout URLs alongside private token/user-info/JWKS URLs.

The application-neutral host still contains no authentication, middleware, header, endpoint, or
problem-response policy. The new backchannel configuration and behavior remain owned by the
authentication feature packages and selected profile templates.
