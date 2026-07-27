using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Development.Capabilities;
using Orbyss.ProgramKit.Development.Diagnostics;
using Orbyss.ProgramKit.Development.Routing;

namespace Orbyss.ProgramKit.Development.Validation;

/// <summary>Validates a routing result against its exact intent and availability inputs.</summary>
public sealed class DevelopmentRoutingResultValidator
    : IDevelopmentRoutingResultValidator
{
    private readonly IProgramKitSemanticValidator<DevelopmentRoutingOutcome> _outcomeValidator;
    private readonly IProgramKitSemanticValidator<CapabilityAvailabilitySnapshot> _snapshotValidator;
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates a routing-result validator with explicit semantic dependencies.</summary>
    public DevelopmentRoutingResultValidator(
        IProgramKitSemanticValidator<DevelopmentRoutingOutcome> outcomeValidator,
        IProgramKitSemanticValidator<CapabilityAvailabilitySnapshot> snapshotValidator,
        IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(outcomeValidator);
        ArgumentNullException.ThrowIfNull(snapshotValidator);
        ArgumentNullException.ThrowIfNull(envelopeValidator);

        _outcomeValidator = outcomeValidator;
        _snapshotValidator = snapshotValidator;
        _envelopeValidator = envelopeValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(DevelopmentRoutingResult value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        DevelopmentValidation.ValidateReference(value.RequestOrIntent, "$.requestOrIntent", diagnostics);
        DevelopmentValidation.ValidateReference(
            value.AvailabilitySnapshot,
            "$.availabilitySnapshot",
            diagnostics);
        if (value.AvailabilitySnapshot is not null
            && !string.Equals(
                value.AvailabilitySnapshot.Identity.Kind,
                "capability-snapshot",
                StringComparison.Ordinal))
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev209,
                "The availability snapshot reference must have PKID kind 'capability-snapshot'.",
                "$.availabilitySnapshot.identity"));
        }

        if (value.Outcome is null)
        {
            diagnostics.Add(DevelopmentValidation.Error(DevelopmentDiagnosticIds.Pkdev203, "A routing outcome is required.", "$.outcome"));
        }
        else
        {
            diagnostics.AddRange(_outcomeValidator.Validate(value.Outcome).Diagnostics);
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates an enveloped routing result and rejects exact payload
    /// references back to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<DevelopmentRoutingResult> envelope)
    {
        var diagnostics = DevelopmentEnvelopeValidation.ValidateEnvelope(
            envelope,
            this,
            _envelopeValidator);
        if (!DevelopmentEnvelopeValidation.TryCreateSelfReference(
                envelope,
                out var selfReference) ||
            envelope.Document is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        DevelopmentEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.RequestOrIntent,
            "/document/requestOrIntent",
            diagnostics);
        DevelopmentEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.AvailabilitySnapshot,
            "/document/availabilitySnapshot",
            diagnostics);
        DevelopmentEnvelopeValidation.RejectRouting(
            selfReference,
            envelope.Document.Outcome,
            "/document/outcome",
            diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates that routing consumed the exact supplied snapshot and selected only an available
    /// capability. No repository access or secondary availability state is consulted.
    /// </summary>
    public ProgramKitValidationResult ValidateAgainst(
        DevelopmentRoutingResult result,
        CapabilityAvailabilitySnapshot snapshot,
        ArtifactReference snapshotReference)
    {
        ArgumentNullException.ThrowIfNull(result);
        ArgumentNullException.ThrowIfNull(snapshot);
        ArgumentNullException.ThrowIfNull(snapshotReference);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(Validate(result).Diagnostics);
        diagnostics.AddRange(_snapshotValidator.Validate(snapshot).Diagnostics);
        DevelopmentValidation.ValidateReference(
            snapshotReference,
            "$.snapshotReference",
            diagnostics);
        if (result.AvailabilitySnapshot != snapshotReference)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev204,
                "Routing must bind the exact supplied availability snapshot.",
                "$.availabilitySnapshot"));
        }

        if (result.Outcome is not null
            && !result.Outcome.NextCapabilities.IsDefault
            && result.Outcome.NextCapabilities.Length == 1)
        {
            var selected = result.Outcome.NextCapabilities[0];
            var availability = snapshot.Capabilities.IsDefault
                ? null
                : snapshot.Capabilities.FirstOrDefault(item =>
                    item is not null && item.CapabilityId == selected.Identity);
            if (availability is null)
            {
                diagnostics.Add(DevelopmentValidation.Error(
                    DevelopmentDiagnosticIds.Pkdev205,
                    $"Selected capability '{selected.Identity.Value}' is absent from the supplied snapshot.",
                    "$.outcome.nextCapabilities[0]"));
            }
            else if (availability.Status != CapabilityAvailabilityStatus.Available)
            {
                diagnostics.Add(DevelopmentValidation.Error(
                    DevelopmentDiagnosticIds.Pkdev206,
                    $"Selected capability '{selected.Identity.Value}' is unavailable in the supplied snapshot.",
                    "$.outcome.nextCapabilities[0]"));
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
