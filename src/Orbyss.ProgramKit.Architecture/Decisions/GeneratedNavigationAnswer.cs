using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Question 6: whether generated navigation is required.</summary>
public sealed record GeneratedNavigationAnswer(
    bool IsRequired,
    ImmutableArray<ProgramKitIdentifier> SourceIds,
    string GenerationRule,
    string Rationale);
