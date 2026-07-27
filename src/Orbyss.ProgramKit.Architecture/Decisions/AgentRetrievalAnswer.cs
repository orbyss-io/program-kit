using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Question 3: whether agents need bounded retrieval of the artifact.</summary>
public sealed record AgentRetrievalAnswer(
    bool IsRequired,
    string RetrievalBoundary,
    string Rationale);
