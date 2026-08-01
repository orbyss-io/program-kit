using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public static class DiagnosticFactory
{
    private const int MaximumInlineDiagnostics = 100;

    public static Diagnostic Create(
        string id,
        OperationPhase phase,
        SafeValue subject,
        SafeValue cause,
        SafeValue consequence,
        IReadOnlyDictionary<string, SafeValue>? parameters = null,
        IReadOnlyList<Remediation>? remediations = null,
        SafeValue? expected = null,
        SafeValue? observed = null,
        IReadOnlyList<EvidenceReference>? evidence = null)
    {
        DiagnosticDefinition definition = DiagnosticCatalog.Entries[id];
        SafeValue safeSubjectValue = DisclosureFilter.Enforce(subject);
        string safeSubject = safeSubjectValue.Value ?? "withheld";
        SafeValue safeCause = DisclosureFilter.Enforce(cause);
        SafeValue safeConsequence = DisclosureFilter.Enforce(consequence);
        IReadOnlyDictionary<string, SafeValue> safeParameters = (parameters ?? new Dictionary<string, SafeValue>(StringComparer.Ordinal))
            .OrderBy(static item => item.Key, StringComparer.Ordinal)
            .ToDictionary(static item => item.Key, static item => DisclosureFilter.Enforce(item.Value), StringComparer.Ordinal);
        SafeValue safeExpected = DisclosureFilter.Enforce(expected ?? DisclosureFilter.PublicText(definition.Expected));
        SafeValue safeObserved = DisclosureFilter.Enforce(observed ?? DisclosureFilter.PublicText(definition.Observed));
        JsonObject occurrenceMaterial = new()
        {
            ["id"] = id,
            ["subject"] = SafeMaterial(safeSubjectValue),
            ["rule"] = definition.MessageKey,
            ["parameters"] = new JsonObject(safeParameters.Select(static item => KeyValuePair.Create<string, JsonNode?>(item.Key, SafeMaterial(item.Value)))),
            ["cause"] = SafeMaterial(safeCause),
            ["expected"] = SafeMaterial(safeExpected),
            ["observed"] = SafeMaterial(safeObserved),
        };
        string occurrence = CanonicalJson.Digest(occurrenceMaterial);
        IReadOnlyList<Remediation> exactRemediations = remediations is { Count: > 0 }
            ? remediations
            : new[] { DefaultRemediation(definition.Disposition, phase, safeSubject) };
        if (exactRemediations.Any(static item =>
            item.RequestDocument is null
            && item.RequestArtifact is null
            && item.RequestArguments is not { Count: > 0 }))
        {
            throw new ArgumentException("Every remediation requires an exact request artifact or a complete inline request payload.", nameof(remediations));
        }

        IReadOnlyList<EvidenceReference> exactEvidence = evidence is { Count: > 0 }
            ? evidence
            : new[] { DiagnosticCatalogArtifacts.EvidenceFor(id) };

        return new Diagnostic(
            id,
            DiagnosticCatalogArtifacts.IdentityFor(id),
            definition.Severity,
            definition.Category,
            phase,
            definition.Disposition,
            occurrence,
            1,
            new[] { safeSubject },
            ProtocolIdentities.Rule(definition.MessageKey),
            definition.MessageKey,
            safeParameters,
            safeCause,
            safeConsequence,
            safeExpected,
            safeObserved,
            exactRemediations,
            exactEvidence);
    }

    public static PrimaryDisposition PrimaryDispositionFor(IEnumerable<Diagnostic> diagnostics)
    {
        PrimaryDisposition[] values = diagnostics.Select(static item => item.Disposition).Distinct().ToArray();
        return values.Length == 1 ? values[0] : PrimaryDisposition.Stop;
    }

    public static DiagnosticView View(IEnumerable<Diagnostic> diagnostics)
    {
        Diagnostic[] complete = diagnostics
            .GroupBy(static item => item.OccurrenceKey, StringComparer.Ordinal)
            .Select(static group => group.First() with { OccurrenceCount = group.Sum(static item => item.OccurrenceCount) })
            .OrderBy(static item => item.Phase)
            .ThenBy(static item => item.Category)
            .ThenByDescending(static item => item.Severity)
            .ThenBy(static item => item.Id, StringComparer.Ordinal)
            .ThenBy(static item => item.OccurrenceKey, StringComparer.Ordinal)
            .ToArray();
        JsonArray collection = new(complete.Select(static item => new JsonObject
        {
            ["id"] = item.Id,
            ["occurrenceKey"] = item.OccurrenceKey,
            ["occurrenceCount"] = item.OccurrenceCount,
        }).ToArray());
        string digest = CanonicalJson.Digest(collection);
        Diagnostic[] returned = complete.Take(MaximumInlineDiagnostics).ToArray();
        return new DiagnosticView(complete.Length, returned.Length, complete.Length - returned.Length, "program-kit.diagnostic-grouping/v1", digest, returned);
    }

    private static Remediation DefaultRemediation(PrimaryDisposition disposition, OperationPhase phase, string subject) => new(
        disposition switch
        {
            PrimaryDisposition.ProvideInput => "provide-input",
            PrimaryDisposition.RequestApproval => "request-approval",
            PrimaryDisposition.Retry => "retry",
            PrimaryDisposition.Repair => "repair",
            PrimaryDisposition.Revise => "revise",
            _ => "stop",
        },
        new[] { subject },
        new[] { "diagnostic-is-current" },
        RequestedEffect.None,
        disposition == PrimaryDisposition.RequestApproval ? new[] { "human-approval" } : Array.Empty<string>(),
        null,
        null,
        new[] { "help" },
        new[] { disposition == PrimaryDisposition.Stop ? "operation-remains-stopped" : "violated-invariant-is-re-evaluated" },
        phase);

    private static JsonObject SafeMaterial(SafeValue value) => new()
    {
        ["classification"] = value.Classification.ToString(),
        ["valueKind"] = value.ValueKind.ToString(),
        ["value"] = value.Value,
        ["redactionReason"] = value.RedactionReason,
        ["policy"] = value.PolicyReference?.Digest,
    };
}
