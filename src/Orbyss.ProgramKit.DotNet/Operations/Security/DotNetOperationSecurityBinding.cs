namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact operation route and named host-policy attachment.</summary>
public sealed record DotNetOperationSecurityBinding(
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("method")] string Method,
    [property: JsonPropertyName("path")] string Path,
    [property: JsonPropertyName("disposition")] DotNetOperationSecurityDisposition Disposition,
    [property: JsonPropertyName("policyIdentity")] ProgramKitIdentifier? PolicyIdentity);
