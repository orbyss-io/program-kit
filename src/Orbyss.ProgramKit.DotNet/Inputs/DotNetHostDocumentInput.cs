namespace Orbyss.ProgramKit.DotNet.Inputs;

/// <summary>Binds one selected host to its exact integrator-document input revision.</summary>
public sealed record DotNetHostDocumentInput(
    [property: JsonPropertyName("hostIdentity")] ProgramKitIdentifier HostIdentity,
    [property: JsonPropertyName("documentRevision")] ArtifactReference DocumentRevision);
