using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

internal sealed record InventoryRow(
    CSharpGateLockInventoryKind Kind,
    CSharpGateLockedContent Content);
