namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Whether and how a rule owner permits suppression.</summary>
public enum CSharpGateSuppressionDisposition
{
    /// <summary>The diagnostic cannot be suppressed.</summary>
    Forbidden,
    /// <summary>Only an exact source-local ledger entry may suppress it.</summary>
    SourceLocalLedger,
}
