# .NET shell transport security v6 to v7

This source-guidance migration adds provider-neutral OIDC, OAuth JWT bearer,
and named ASP.NET Core host-policy mechanics without inventing identity-provider
or consumer-domain authorization meaning.

For each v6 host:

1. Add `security: null` when no reviewed transport security profile exists.
2. Enable security only for API hosts. Select the confidential interactive
   authorization-code-with-PKCE profile, the RFC 9068 JWT resource-server
   profile, or both.
3. Declare exact authentication scheme defaults. Preserve provider claim names;
   do not infer roles, grants, domain principals, or authority conclusions.
4. Keep confidential client material outside the shell. Bind a classified
   configuration-text secret reference or a classified assertion-service
   reference. Never persist a secret, certificate, key, assertion, or token.
5. Require HTTPS metadata, issuer and audience validation, signed asymmetric
   token algorithms, expiry validation, nonce, state, secure correlation
   cookies, and explicit pushed-authorization behavior.
6. Give every operation exactly one route/method binding: explicit anonymous
   access or one exact named host policy. Program Kit may register only the
   generic authenticated-transport policy; consumers own all other policy
   meaning.
7. Generate authentication before operation authorization. Failed anonymous
   authentication challenges through the selected framework scheme; failed
   authenticated authorization forbids through that scheme.
8. Project the exact schemes and operation attachments into OpenAPI. Missing,
   additional, or mismatched runtime and OpenAPI declarations fail generation.
9. Treat identity-provider products as optional adapters. Keycloak, Entra ID,
   and other providers bind through the same standard protocol contracts.

Public browser clients, client credentials, and token exchange are introduced
by their own approved work units. Device flow, CIBA, FAPI, and DPoP remain
deferred.
