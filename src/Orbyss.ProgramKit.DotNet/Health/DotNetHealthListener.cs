namespace Orbyss.ProgramKit.DotNet.Health;

/// <summary>Exact dedicated health listener and transport policy references.</summary>
public sealed record DotNetHealthListener(
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("scheme")] string Scheme,
    [property: JsonPropertyName("address")] string Address,
    [property: JsonPropertyName("port")] int Port,
    [property: JsonPropertyName("exposure")] DotNetHealthExposure Exposure,
    [property: JsonPropertyName("authenticationRevision")] ArtifactReference? AuthenticationRevision,
    [property: JsonPropertyName("tlsRevision")] ArtifactReference? TlsRevision,
    [property: JsonPropertyName("hostFilterRevision")] ArtifactReference? HostFilterRevision);
