using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A term whose meaning is owned by the containing domain.</summary>
public sealed record VocabularyTermDefinition(
    string Term,
    string Meaning,
    ImmutableArray<string> AcceptedAliases);
