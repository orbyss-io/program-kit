using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Development;

/// <summary>Validates a human-session supplied capability availability snapshot.</summary>
public sealed class CapabilityAvailabilitySnapshotValidator
    : IProgramKitSemanticValidator<CapabilityAvailabilitySnapshot>
{
    /// <summary>The only canonical capability-index source path.</summary>
    public const string CanonicalIndexPath = ".agents/capabilities/INDEX.md";

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(CapabilityAvailabilitySnapshot value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (!string.Equals(value.SourcePath, CanonicalIndexPath, StringComparison.Ordinal))
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev101,
                $"Capability availability must bind the exact canonical source path '{CanonicalIndexPath}'.",
                "$.sourcePath"));
        }

        if (string.IsNullOrWhiteSpace(value.SourceDigest.Value))
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev102,
                "The exact SHA-256 digest of the capability index is required.",
                "$.sourceDigest"));
        }

        DevelopmentValidation.RequireIdentifier(value.SupplierId, "$.supplierId", diagnostics);
        if (value.SuppliedAt == default)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev103,
                "A snapshot time supplied by the human-session capability is required.",
                "$.suppliedAt"));
        }

        if (value.Capabilities.IsDefault)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev104,
                "Capability availability entries must be initialized.",
                "$.capabilities"));
        }
        else
        {
            var ids = new HashSet<ProgramKitIdentifier>();
            for (var index = 0; index < value.Capabilities.Length; index++)
            {
                var capability = value.Capabilities[index];
                var path = $"$.capabilities[{index}]";
                if (capability is null)
                {
                    diagnostics.Add(DevelopmentValidation.Error(
                        DevelopmentDiagnosticIds.Pkdev105,
                        "A capability availability entry cannot be null.",
                        path));
                    continue;
                }

                DevelopmentValidation.RequireIdentifier(capability.CapabilityId, $"{path}.capabilityId", diagnostics);
                if (!string.Equals(
                        capability.CapabilityId.Kind,
                        "capability",
                        StringComparison.Ordinal))
                {
                    diagnostics.Add(DevelopmentValidation.Error(
                        DevelopmentDiagnosticIds.Pkdev108,
                        "Capability availability must identify a PKID kind 'capability'.",
                        $"{path}.capabilityId"));
                }

                if (!Enum.IsDefined(capability.Status))
                {
                    diagnostics.Add(DevelopmentValidation.Error(
                        DevelopmentDiagnosticIds.Pkdev107,
                        "Capability availability status must be a defined value.",
                        $"{path}.status"));
                }

                if (!ids.Add(capability.CapabilityId))
                {
                    diagnostics.Add(DevelopmentValidation.Error(
                        DevelopmentDiagnosticIds.Pkdev106,
                        $"Capability '{capability.CapabilityId.Value}' occurs more than once.",
                        $"{path}.capabilityId"));
                }
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>Validates an enveloped capability availability snapshot.</summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<CapabilityAvailabilitySnapshot> envelope)
    {
        var diagnostics = DevelopmentEnvelopeValidation.ValidateEnvelope(envelope, this);
        return ProgramKitValidationResult.From(diagnostics);
    }
}

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

/// <summary>Validates a routing result against its exact intent and availability inputs.</summary>
public sealed class DevelopmentRoutingResultValidator
    : IProgramKitSemanticValidator<DevelopmentRoutingResult>
{
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
            diagnostics.AddRange(new DevelopmentRoutingOutcomeValidator().Validate(value.Outcome).Diagnostics);
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
        var diagnostics = DevelopmentEnvelopeValidation.ValidateEnvelope(envelope, this);
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
        diagnostics.AddRange(new CapabilityAvailabilitySnapshotValidator().Validate(snapshot).Diagnostics);
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

/// <summary>Validates a digest-bound, evidence-only development receipt.</summary>
public sealed class DevelopmentReceiptValidator : IProgramKitSemanticValidator<DevelopmentReceipt>
{
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
        var diagnostics = DevelopmentEnvelopeValidation.ValidateEnvelope(envelope, this);
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
        Planning.PrincipalReference? value,
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

    private static void ValidateResult(
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
            diagnostics.AddRange(new DevelopmentRoutingOutcomeValidator().Validate(value.Routing).Diagnostics);
        }
    }
}

internal static class DevelopmentEnvelopeValidation
{
    internal static ImmutableArray<ProgramKitDiagnostic>.Builder ValidateEnvelope<TDocument>(
        ArtifactEnvelope<TDocument> envelope,
        IProgramKitSemanticValidator<TDocument> validator)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(
            new ArtifactEnvelopeValidator<TDocument>(validator)
                .Validate(envelope)
                .Diagnostics);
        return diagnostics;
    }

    internal static bool TryCreateSelfReference<TDocument>(
        ArtifactEnvelope<TDocument>? envelope,
        out ArtifactReference selfReference)
    {
        if (envelope?.Artifact is null || envelope.Integrity is null)
        {
            selfReference = null!;
            return false;
        }

        selfReference = new ArtifactReference(
            envelope.Artifact.Id,
            envelope.Artifact.Version,
            envelope.Integrity.Digest);
        return true;
    }

    internal static void Reject(
        ArtifactReference selfReference,
        ArtifactReference? candidate,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (candidate == selfReference)
        {
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev307,
                "A development artifact must not embed its own exact identity, version, and digest reference.",
                path));
        }
    }

    internal static void RejectAll(
        ArtifactReference selfReference,
        ImmutableArray<ArtifactReference> candidates,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (candidates.IsDefault)
        {
            return;
        }

        for (var index = 0; index < candidates.Length; index++)
        {
            Reject(
                selfReference,
                candidates[index],
                string.Concat(path, "/", index),
                diagnostics);
        }
    }

    internal static void RejectRouting(
        ArtifactReference selfReference,
        DevelopmentRoutingOutcome? routing,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (routing is null)
        {
            return;
        }

        RejectAll(
            selfReference,
            routing.NextCapabilities,
            string.Concat(path, "/nextCapabilities"),
            diagnostics);
    }
}

internal static class DevelopmentValidation
{
    internal static ProgramKitDiagnostic Error(string id, string message, string path) =>
        new(id, ProgramKitDiagnosticSeverity.Error, message, path);

    internal static void RequireText(
        string? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev001, "A non-empty value is required.", path));
        }
    }

    internal static void RequireIdentifier(
        ProgramKitIdentifier value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value.Value))
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev002, "A Program Kit identifier is required.", path));
        }
    }

    internal static void ValidateReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev003, "An exact artifact reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev004, "An exact semantic version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev005, "An exact SHA-256 digest is required.", $"{path}.digest"));
        }
    }

    internal static void ValidateReferences(
        ImmutableArray<ArtifactReference> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev006, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<ArtifactReference>();
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            ValidateReference(value, $"{path}[{index}]", diagnostics);
            if (value is not null && !seen.Add(value))
            {
                diagnostics.Add(Error(DevelopmentDiagnosticIds.Pkdev007, "Exact artifact references must be unique.", $"{path}[{index}]"));
            }
        }
    }
}
