using System.Text.Json.Serialization;
using Orbyss.ProgramKit.DotNet.Documentation;

namespace Orbyss.ProgramKit.DotNet.Documentation.Worker;

/// <summary>Deliberately small deterministic Worker integrator document.</summary>
public sealed record OpenWorkerDocument(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("documentVersion")] SemanticVersion DocumentVersion,
    [property: JsonPropertyName("info")] IntegratorDocumentInfo Info,
    [property: JsonPropertyName("hostRevision")] ArtifactReference HostRevision,
    [property: JsonPropertyName("workers")] ImmutableArray<OpenWorkerEntry> Workers,
    [property: JsonPropertyName("compatibility")] ArtifactCompatibility Compatibility,
    [property: JsonPropertyName("provenance")] IntegratorDocumentProvenance Provenance);
