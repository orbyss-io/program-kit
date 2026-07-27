using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Development.Diagnostics;
using Orbyss.ProgramKit.Development.Routing;

namespace Orbyss.ProgramKit.Development.Validation;

/// <summary>Validates routing cardinality and the deliberate absence of delegated authority.</summary>
public sealed class DevelopmentRoutingOutcomeValidator
    : IProgramKitSemanticValidator<DevelopmentRoutingOutcome>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(DevelopmentRoutingOutcome value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        DevelopmentValidation.RequireText(value.Reason, "$.reason", diagnostics);
        DevelopmentValidation.ValidateReferences(value.NextCapabilities, "$.nextCapabilities", diagnostics);
        if (!Enum.IsDefined(value.Kind))
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev207,
                "Development routing outcome kind must be a defined value.",
                "$.kind"));
        }

        if (!value.NextCapabilities.IsDefault && value.NextCapabilities.Length > 1)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev201,
                "A routing outcome may select at most one next capability.",
                "$.nextCapabilities"));
        }

        if (!value.NextCapabilities.IsDefault)
        {
            for (var index = 0; index < value.NextCapabilities.Length; index++)
            {
                var capability = value.NextCapabilities[index];
                if (capability is not null
                    && !string.Equals(
                        capability.Identity.Kind,
                        "capability",
                        StringComparison.Ordinal))
                {
                    diagnostics.Add(DevelopmentValidation.Error(
                        DevelopmentDiagnosticIds.Pkdev208,
                        "A routed next capability must have PKID kind 'capability'.",
                        $"$.nextCapabilities[{index}].identity"));
                }
            }
        }

        if (value.Kind is DevelopmentRoutingOutcomeKind.HumanDecisionRequired
            or DevelopmentRoutingOutcomeKind.FlowUnavailable
            && !value.NextCapabilities.IsDefaultOrEmpty)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev202,
                "Human-decision-required and flow-unavailable outcomes cannot select a capability.",
                "$.nextCapabilities"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
