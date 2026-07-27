using System.Collections.Immutable;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>
/// Exact offline binding request. The candidate lock is accepted only when
/// every explicitly listed local asset still has its bound digest.
/// </summary>
public sealed record CSharpGateBindRequest(
    string RepositoryRoot,
    CSharpBuildGateSelectionLockDocument CandidateLock,
    ImmutableArray<CSharpGateLocalAssetBinding> LocalAssets);
