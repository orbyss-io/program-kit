using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A source project and its explicit architecture ownership.</summary>
public sealed record ProjectDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    string ProjectPath,
    ImmutableArray<ProgramKitIdentifier> ComponentIds,
    ImmutableArray<ProgramKitIdentifier> ProjectReferenceIds,
    ProgramKitIdentifier? PackageId);
