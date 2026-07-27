using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Middleware;

/// <summary>Explicit non-durable context for one pre-acceptance request.</summary>
public sealed record TaskDispatchContext(
    ArtifactReference RequestRevision,
    ArtifactReference DefinitionRevision,
    Type RequestType,
    object Request);
