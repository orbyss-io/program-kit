using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

/// <summary>An exact path/content binding in a selection lock.</summary>
public sealed record CSharpGateLockedContent(
    string RepositoryRelativePath,
    Sha256Digest Digest);
