namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>The explicit role of a Planning 3.0 implementation work unit.</summary>
public enum PlanWorkUnitKind
{
    /// <summary>Establishes and activates a selected consumer-owned gate.</summary>
    GateEstablishment,
    /// <summary>Mutates the approved product implementation.</summary>
    Product,
    /// <summary>Performs final closure and whole-plan verification.</summary>
    Closure,
}
