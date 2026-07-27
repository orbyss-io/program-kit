using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>One typed condition parameter bound to an exact controlled input.</summary>
public sealed record CSharpGateConditionParameter(
    string Name,
    string Value,
    Sha256Digest InputDigest);
