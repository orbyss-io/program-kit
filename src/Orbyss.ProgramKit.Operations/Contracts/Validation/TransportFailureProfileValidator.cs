using Orbyss.ProgramKit.Operations.Contracts.Diagnostics;
using Orbyss.ProgramKit.Operations.Contracts.Transport;

namespace Orbyss.ProgramKit.Operations.Contracts.Validation;

/// <summary>Validates explicit, finite, publicly disclosed transport-failure meaning.</summary>
public sealed class TransportFailureProfileValidator :
    IProgramKitSemanticValidator<TransportFailureProfile>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TransportFailureProfile value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        OperationsValidation.ValidateReference(
            value.ProfileRevision,
            "$.profileRevision",
            diagnostics);
        if (value.Failures.IsDefaultOrEmpty)
        {
            diagnostics.Add(Invalid(
                "A finite transport-failure catalog is required.",
                "$.failures"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        var identities = new HashSet<string>(StringComparer.Ordinal);
        foreach (var failure in value.Failures)
        {
            if (failure is null ||
                !identities.Add(failure.Identity.Value) ||
                failure.StatusCode is < 400 or > 599 ||
                failure.Type is null ||
                !failure.Type.IsAbsoluteUri ||
                failure.Type.Scheme != Uri.UriSchemeHttps ||
                !SafeText(failure.Title, 128) ||
                !SafeText(failure.ProductionDetail, 512) ||
                !SafeText(failure.DevelopmentDetail, 512) ||
                !Enum.IsDefined(failure.Disclosure))
            {
                diagnostics.Add(Invalid(
                    "Each failure requires a unique identity, HTTP 400-599 status, absolute HTTPS type, bounded public text, and explicit disclosure.",
                    "$.failures"));
                continue;
            }

            OperationsValidation.ValidateReference(
                failure.ProblemSchemaRevision,
                "$.failures.problemSchemaRevision",
                diagnostics,
                "schema");
        }

        var fallback = value.Failures.Where(
            failure => failure is not null &&
                       failure.Identity == value.GenericFallbackIdentity).ToArray();
        if (fallback.Length != 1 || fallback[0].StatusCode != 500)
        {
            diagnostics.Add(Invalid(
                "The generic fallback must resolve exactly once and use HTTP 500.",
                "$.genericFallbackIdentity"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static bool SafeText(string value, int maximumLength) =>
        !string.IsNullOrWhiteSpace(value) &&
        value.Length <= maximumLength &&
        !value.Any(static character => char.IsControl(character));

    private static ProgramKitDiagnostic Invalid(string message, string path) =>
        new(
            OperationsDiagnosticIds.InvalidTransportFailure,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path);
}
