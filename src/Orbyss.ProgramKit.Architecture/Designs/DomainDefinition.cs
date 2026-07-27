using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A domain and its exclusively owned vocabulary.</summary>
public sealed record DomainDefinition(
    ProgramKitIdentifier Identity,
    string Purpose,
    ImmutableArray<VocabularyTermDefinition> Vocabulary);
