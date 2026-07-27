namespace Orbyss.ProgramKit.DotNet.Health;

/// <summary>One explicitly exposed and isolated health endpoint.</summary>
public sealed record DotNetHealthEndpoint(
    [property: JsonPropertyName("kind")] DotNetHealthEndpointKind Kind,
    [property: JsonPropertyName("path")] string Path,
    [property: JsonPropertyName("listenerIdentity")] ProgramKitIdentifier ListenerIdentity,
    [property: JsonPropertyName("includeTags")] ImmutableArray<string> IncludeTags,
    [property: JsonPropertyName("excludeTags")] ImmutableArray<string> ExcludeTags,
    [property: JsonPropertyName("statusCodes")] DotNetHealthStatusCodeMap StatusCodes,
    [property: JsonPropertyName("responseProfileRevision")] ArtifactReference ResponseProfileRevision,
    [property: JsonPropertyName("cachePolicy")] string CachePolicy,
    [property: JsonPropertyName("authorizationRevision")] ArtifactReference AuthorizationRevision,
    [property: JsonPropertyName("documentation")] DotNetHealthDocumentationSelection Documentation);
