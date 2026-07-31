# .NET OAuth service-client migration from shell v8 to v9

Shell v9 adds two separate provider-neutral transport profiles:
`oauthClientCredentials` and `oauthTokenExchanges`. Existing v8 security
settings retain their meaning.

Migration must explicitly select each token endpoint, client identity,
authentication reference and method, single resource, single audience, exact
scope set, issued token type, bounded lifetime, cache, cancellation, outage
and redaction behavior. No client secret or token value belongs in the shell.

Every token exchange must identify a non-ambient subject-token source and
token type. Delegation requires a distinct actor-token source and type;
impersonation forbids an actor token. The mode is transport intent only and
does not establish domain permission, downscope, on-behalf-of authority,
delegation or impersonation semantics.

Generated clients use explicit cancellation, no automatic retry, bounded
in-memory caching whose key covers every selected security dimension, and
redacted outcome-only diagnostics. Tokens remain runtime transport security
material and never become generated source or durable evidence.
