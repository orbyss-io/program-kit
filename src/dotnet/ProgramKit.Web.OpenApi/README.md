# ProgramKit.Web.OpenApi

An optional `IWebShellFeature` that registers the Program Kit OpenAPI document and maps it at
`/_program-kit/openapi/{documentName}.json` within the active shell. Consumers can replace or omit
the feature without changing `ProgramKit.Host`.
