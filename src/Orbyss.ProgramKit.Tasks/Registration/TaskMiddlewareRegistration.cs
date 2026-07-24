using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Exact task middleware registration and ordering constraints.</summary>
public sealed record TaskMiddlewareRegistration(
    ArtifactReference Revision,
    TaskMiddlewarePhase Phase,
    Type MiddlewareType,
    int Priority,
    ImmutableArray<ProgramKitIdentifier> Before,
    ImmutableArray<ProgramKitIdentifier> After);
