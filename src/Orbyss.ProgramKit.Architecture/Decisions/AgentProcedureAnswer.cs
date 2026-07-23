using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Question 4: whether the artifact carries agent judgment or procedure.</summary>
public sealed record AgentProcedureAnswer(
    bool IsRequired,
    string HumanStartBoundary,
    string ProcedureBoundary,
    string Rationale);
