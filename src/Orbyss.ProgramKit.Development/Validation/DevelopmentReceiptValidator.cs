using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Development.Diagnostics;
using Orbyss.ProgramKit.Development.Receipts;
using Orbyss.ProgramKit.Development.Routing;
using Orbyss.ProgramKit.Planning.Approvals;

namespace Orbyss.ProgramKit.Development.Validation;

/// <summary>Validates a digest-bound, evidence-only development receipt.</summary>
public sealed class DevelopmentReceiptValidator : IDevelopmentReceiptValidator
{
    private readonly IProgramKitSemanticValidator<DevelopmentRoutingOutcome> _routingOutcomeValidator;
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates a receipt validator with an explicit routing-outcome dependency.</summary>
    public DevelopmentReceiptValidator(
        IProgramKitSemanticValidator<DevelopmentRoutingOutcome> routingOutcomeValidator,
        IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(routingOutcomeValidator);
        ArgumentNullException.ThrowIfNull(envelopeValidator);

        _routingOutcomeValidator = routingOutcomeValidator;
        _envelopeValidator = envelopeValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(DevelopmentReceipt value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        DevelopmentValidation.ValidateReference(value.Capability, "$.capability", diagnostics);
        if (value.Capability is not null
            && !string.Equals(value.Capability.Identity.Kind, "capability", StringComparison.Ordinal))
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev306,
                "A development receipt capability must have PKID kind 'capability'.",
                "$.capability.identity"));
        }

        DevelopmentValidation.ValidateReference(value.RequestOrIntent, "$.requestOrIntent", diagnostics);
        DevelopmentValidation.ValidateReferences(value.ConsumedArtifacts, "$.consumedArtifacts", diagnostics);
        DevelopmentValidation.RequireIdentifier(value.ProducerId, "$.producerId", diagnostics);
        DevelopmentValidation.RequireText(value.CorrelationId, "$.correlationId", diagnostics);
        if (value.SuppliedAt == default)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev301,
                "A receipt time supplied by the human-session boundary is required.",
                "$.suppliedAt"));
        }

        ValidatePrincipal(value.Principal, diagnostics);
        ValidateResult(value.Result, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates an enveloped development receipt and rejects exact payload
    /// references back to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<DevelopmentReceipt> envelope)
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
            envelope.Document.Capability,
            "/document/capability",
            diagnostics);
        DevelopmentEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.RequestOrIntent,
            "/document/requestOrIntent",
            diagnostics);
        DevelopmentEnvelopeValidation.RejectAll(
            selfReference,
            envelope.Document.ConsumedArtifacts,
            "/document/consumedArtifacts",
            diagnostics);
        if (envelope.Document.Result is { } result)
        {
            DevelopmentEnvelopeValidation.RejectAll(
                selfReference,
                result.ProducedArtifacts,
                "/document/result/producedArtifacts",
                diagnostics);
            DevelopmentEnvelopeValidation.RejectRouting(
                selfReference,
                result.Routing,
                "/document/result/routing",
                diagnostics);
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Applies an explicit lower time bound, allowing callers to reject backdated receipt claims
    /// without reading an ambient clock or capability registry.
    /// </summary>
    public ProgramKitValidationResult ValidateNotBefore(
        DevelopmentReceipt receipt,
        DateTimeOffset earliestPermittedTime)
    {
        ArgumentNullException.ThrowIfNull(receipt);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(Validate(receipt).Diagnostics);
        if (receipt.SuppliedAt < earliestPermittedTime)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev302,
                "The receipt predates the explicitly supplied capability boundary.",
                "$.suppliedAt"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidatePrincipal(
        PrincipalReference? value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev303,
                "A principal supplied by the human-session boundary is required.",
                "$.principal"));
            return;
        }

        DevelopmentValidation.RequireText(value.Kind, "$.principal.kind", diagnostics);
        DevelopmentValidation.RequireText(value.Provider, "$.principal.provider", diagnostics);
        DevelopmentValidation.RequireText(value.Identifier, "$.principal.identifier", diagnostics);
        DevelopmentValidation.RequireText(value.Role, "$.principal.role", diagnostics);
    }

    private void ValidateResult(
        DevelopmentResult? value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(DevelopmentValidation.Error(DevelopmentDiagnosticIds.Pkdev304, "A development result is required.", "$.result"));
            return;
        }

        DevelopmentValidation.RequireText(value.Summary, "$.result.summary", diagnostics);
        if (!Enum.IsDefined(value.Kind))
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev305,
                "Development result kind must be a defined value.",
                "$.result.kind"));
        }

        DevelopmentValidation.ValidateReferences(
            value.ProducedArtifacts,
            "$.result.producedArtifacts",
            diagnostics);
        if (value.Routing is not null)
        {
            diagnostics.AddRange(_routingOutcomeValidator.Validate(value.Routing).Diagnostics);
        }
    }
}
