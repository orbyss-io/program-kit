using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Question 5: whether the artifact explains or records a human decision.</summary>
public sealed record HumanCommunicationAnswer(
    bool IsRequired,
    string Audience,
    string DecisionAuthorityBoundary,
    string Rationale);
