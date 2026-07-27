using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Schemas;

/// <summary>Identifies the schema contract governing an envelope.</summary>
/// <param name="SchemaId">The schema PKID.</param>
/// <param name="SchemaVersion">The full schema SemVer version.</param>
public sealed record ArtifactContract(
    ProgramKitIdentifier SchemaId,
    SemanticVersion SchemaVersion);
