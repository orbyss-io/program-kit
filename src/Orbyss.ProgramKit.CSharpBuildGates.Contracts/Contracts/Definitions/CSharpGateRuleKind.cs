namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>The only policy-rule ownership kinds supported by a gate.</summary>
public enum CSharpGateRuleKind
{
    /// <summary>The invariant and diagnostic remain owned by Program Kit.</summary>
    ProgramKitPublicContract,
    /// <summary>The invariant and diagnostic are owned by the consumer.</summary>
    ConsumerOwned,
}
