namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Restrictive, metadata-only HTTP diagnostic logging selection.</summary>
public sealed record DotNetHttpDiagnosticProfile(
    [property: JsonPropertyName("enabled")] bool Enabled,
    [property: JsonPropertyName("includeMethod")] bool IncludeMethod,
    [property: JsonPropertyName("includePath")] bool IncludePath,
    [property: JsonPropertyName("includeStatusCode")] bool IncludeStatusCode,
    [property: JsonPropertyName("includeDuration")] bool IncludeDuration,
    [property: JsonPropertyName("requestHeaders")] ImmutableArray<string> RequestHeaders,
    [property: JsonPropertyName("responseHeaders")] ImmutableArray<string> ResponseHeaders,
    [property: JsonPropertyName("includeRequestBody")] bool IncludeRequestBody,
    [property: JsonPropertyName("includeResponseBody")] bool IncludeResponseBody);
