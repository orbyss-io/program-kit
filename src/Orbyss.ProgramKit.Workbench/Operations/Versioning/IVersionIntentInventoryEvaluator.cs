namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Validates exact closed inventory coverage over bounded observations.</summary>
public interface IVersionIntentInventoryEvaluator
{
    /// <summary>Returns deterministic diagnostics without scanning or classifying sources.</summary>
    ProgramKitValidationResult Evaluate(
        VersionIntentInventoryValidationRequest request);
}
