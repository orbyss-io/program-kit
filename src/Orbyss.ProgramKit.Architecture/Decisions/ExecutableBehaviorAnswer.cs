using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Question 1: whether the outcome requires executable behavior.</summary>
public sealed record ExecutableBehaviorAnswer(
    bool IsRequired,
    string Rationale);
