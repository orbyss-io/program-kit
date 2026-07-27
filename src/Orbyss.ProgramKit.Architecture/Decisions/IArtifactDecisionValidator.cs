namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Validates complete artifact decisions at a caller-selected document path.</summary>
public interface IArtifactDecisionValidator :
    IProgramKitSemanticValidator<ArtifactDecision>
{
    /// <summary>Validates a decision with diagnostics rooted at the supplied path.</summary>
    ProgramKitValidationResult Validate(ArtifactDecision value, string path);
}
