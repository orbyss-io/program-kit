using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

internal sealed record CSharpGateLockInventorySet(
    ImmutableArray<CSharpGateLockedContent> Project,
    ImmutableArray<CSharpGateLockedContent> PhysicalSource,
    ImmutableArray<CSharpGateLockedContent> GeneratedSource,
    ImmutableArray<CSharpGateLockedContent> Reference,
    ImmutableArray<CSharpGateLockedContent> AdditionalFile,
    ImmutableArray<CSharpGateLockedContent> AnalyzerConfiguration)
{
    public IEnumerable<CSharpGateLocalAssetBinding> All =>
        Project
            .Concat(PhysicalSource)
            .Concat(GeneratedSource)
            .Concat(Reference)
            .Concat(AdditionalFile)
            .Concat(AnalyzerConfiguration)
            .Select(static content => new CSharpGateLocalAssetBinding(
                content.RepositoryRelativePath,
                content.Digest));
}
