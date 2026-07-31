# .NET shell transport failures v5 to v6

This source-guidance migration adds explicit ASP.NET Core transport-failure
composition without inventing consumer-domain error meaning.

For each v5 host:

1. Add `transportFailures: null` when the host has no reviewed transport
   failure profile. This preserves the previous response behavior.
2. Enable the profile only for an API host. Declare a finite consumer-owned
   failure catalog with one exact HTTP 500 generic fallback.
3. Give every declared failure a stable identity, HTTP 400-599 status,
   absolute HTTPS Problem Details type, bounded public title and fixed
   production/development detail, exact Problem Details schema, and explicit
   public-disclosure assertion.
4. Bind non-generic .NET exception types only through explicit ordered
   declarations. Do not infer status or meaning from names, namespaces,
   messages, inheritance scans, reflection discovery, or provider payloads.
5. Do not bind `Exception`, `OperationCanceledException`, or
   `TaskCanceledException`. A request-aborted cancellation is classified as a
   client disconnect and aborted without manufacturing a response. Other
   cancellation remains unhandled unless a future reviewed profile defines it.
6. Leave an exception unhandled when response headers have already started.
   Never rewrite a partial response.
7. Register `AddProblemDetails`, ordered singleton `IExceptionHandler`
   implementations, and `UseExceptionHandler` before endpoint execution.
   Status-code pages are an explicit optional selection.
8. Explicitly suppress .NET 10 framework diagnostics for handled exceptions
   and emit one sanitized Program Kit outcome. Never log raw exception
   messages, stack traces, request bodies, headers, claims, configuration, or
   secret material.
9. Project every runtime failure contract into every owned operation's OpenAPI
   Problem Details responses. Missing, extra, or mismatched declarations fail
   generation.

Development detail is fixed reviewed text from the contract, not
`Exception.Message`. Content negotiation may yield an empty failure body when
no registered Problem Details writer accepts the request; the declared status
remains authoritative.
