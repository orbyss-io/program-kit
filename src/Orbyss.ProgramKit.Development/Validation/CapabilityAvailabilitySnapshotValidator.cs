using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Development.Capabilities;
using Orbyss.ProgramKit.Development.Diagnostics;

namespace Orbyss.ProgramKit.Development.Validation;

/// <summary>Validates a human-session supplied capability availability snapshot.</summary>
public sealed class CapabilityAvailabilitySnapshotValidator
    : IArtifactEnvelopeSemanticValidator<CapabilityAvailabilitySnapshot>
{
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates a snapshot validator with explicit envelope validation.</summary>
    public CapabilityAvailabilitySnapshotValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(envelopeValidator);
        _envelopeValidator = envelopeValidator;
    }

    /// <summary>The only canonical capability-index source path.</summary>
    public const string CanonicalIndexPath =
        ".agent-capabilities/capabilities/INDEX.md";

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
        var diagnostics = DevelopmentEnvelopeValidation.ValidateEnvelope(
            envelope,
            this,
            _envelopeValidator);
        return ProgramKitValidationResult.From(diagnostics);
    }
}
