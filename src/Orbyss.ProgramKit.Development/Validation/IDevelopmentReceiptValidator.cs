using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Development.Receipts;

namespace Orbyss.ProgramKit.Development.Validation;

/// <summary>
/// Validates development receipts, their envelopes, and caller-supplied
/// chronology boundaries.
/// </summary>
public interface IDevelopmentReceiptValidator :
    IArtifactEnvelopeSemanticValidator<DevelopmentReceipt>
{
    /// <summary>
    /// Validates that a receipt was supplied no earlier than the caller's
    /// permitted boundary.
    /// </summary>
    ProgramKitValidationResult ValidateNotBefore(
        DevelopmentReceipt receipt,
        DateTimeOffset earliestPermittedTime);
}
