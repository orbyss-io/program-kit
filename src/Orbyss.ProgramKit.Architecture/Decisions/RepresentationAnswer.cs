using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Question 7: canonical versus projected representation.</summary>
public sealed record RepresentationAnswer(
    ArtifactRepresentationRole Role,
    ProgramKitIdentifier? CanonicalArtifactId,
    string ProjectionRule,
    string LossPolicy);
