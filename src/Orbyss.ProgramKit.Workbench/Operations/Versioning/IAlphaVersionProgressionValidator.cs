namespace Orbyss.ProgramKit.Workbench.Operations.Versioning;

/// <summary>Validates explicit proposals without selecting or mutating versions.</summary>
public interface IAlphaVersionProgressionValidator
{
    /// <summary>Checks one proposal against one exact replaceable policy.</summary>
    ProgramKitValidationResult Validate(AlphaVersionProgressionDocument document);
}
