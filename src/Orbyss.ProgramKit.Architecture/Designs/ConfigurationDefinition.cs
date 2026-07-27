using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>An explicitly owned configuration surface.</summary>
public sealed record ConfigurationDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ArtifactReference Schema,
    string Scope,
    string SecretsPolicy,
    string CompatibilityPolicy);
