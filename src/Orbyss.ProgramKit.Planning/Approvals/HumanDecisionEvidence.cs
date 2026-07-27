using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>References evidence supplied with a human decision.</summary>
public sealed record HumanDecisionEvidence(
    string Kind,
    string Provider,
    string ReferenceId,
    Sha256Digest? Digest);
