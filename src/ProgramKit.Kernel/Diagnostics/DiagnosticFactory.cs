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
        string subject,
        string cause,
        string consequence,
        IReadOnlyDictionary<string, SafeValue>? parameters = null,
        IReadOnlyList<Remediation>? remediations = null,
        SafeValue? expected = null,
        SafeValue? observed = null,
        IReadOnlyList<EvidenceReference>? evidence = null)
    {
        DiagnosticDefinition definition = DiagnosticCatalog.Entries[id];
        string safeSubject = DisclosureFilter.SafeLogicalValue(subject);
        SafeValue safeCause = DisclosureFilter.Classify(cause);
        SafeValue safeConsequence = DisclosureFilter.Classify(consequence);
        IReadOnlyDictionary<string, SafeValue> safeParameters = (parameters ?? new Dictionary<string, SafeValue>(StringComparer.Ordinal))
            .OrderBy(static item => item.Key, StringComparer.Ordinal)
            .ToDictionary(static item => item.Key, static item => item.Value, StringComparer.Ordinal);
        SafeValue safeExpected = expected ?? new SafeValue(SafeValueClassification.Public, SafeValueKind.Text, definition.Expected);
        SafeValue safeObserved = observed ?? new SafeValue(SafeValueClassification.Public, SafeValueKind.Text, definition.Observed);
        JsonObject occurrenceMaterial = new()
        {
            ["id"] = id,
            ["subject"] = safeSubject,
            ["rule"] = definition.MessageKey,
            ["parameters"] = new JsonObject(safeParameters.Select(static item => KeyValuePair.Create<string, JsonNode?>(item.Key, SafeMaterial(item.Value)))),
            ["cause"] = SafeMaterial(safeCause),
            ["expected"] = SafeMaterial(safeExpected),
            ["observed"] = SafeMaterial(safeObserved),
        };
        string occurrence = CanonicalJson.Digest(occurrenceMaterial);
        string catalogAuthority = id.StartsWith("program-kit.provider.dotnet/", StringComparison.Ordinal)
            ? "orbyss.program-kit.dotnet"
            : "orbyss.program-kit";

        return new Diagnostic(
            id,
            ProtocolIdentities.Catalog(catalogAuthority, catalogAuthority.EndsWith("dotnet", StringComparison.Ordinal) ? "provider" : "kernel"),
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
            remediations is { Count: > 0 } ? remediations : new[] { DefaultRemediation(definition.Disposition, phase, safeSubject) },
            evidence ?? Array.Empty<EvidenceReference>());
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
