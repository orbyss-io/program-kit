using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>
/// Complete 0.1.0-alpha.1 bind request emitted by the lock scaffolder.
/// </summary>
public sealed record CSharpGateBindRequestAlpha1(
    SemanticVersion Version,
    string RepositoryRoot,
    string DefinitionRepositoryRelativePath,
    CSharpGateLockIntent LockIntent,
    CSharpBuildGateSelectionLockDocumentAlpha1 CandidateLock,
    ImmutableArray<CSharpGateLocalAssetBinding> LocalAssets);
