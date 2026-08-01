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
        IReadOnlyDictionary<string, string>? parameters = null,
        IReadOnlyList<Remediation>? remediations = null)
    {
        DiagnosticDefinition definition = DiagnosticCatalog.Entries[id];
        string safeSubject = DisclosureFilter.SafeLogicalValue(subject);
        string safeCause = DisclosureFilter.SafeText(cause);
        IReadOnlyDictionary<string, string> safeParameters = (parameters ?? new Dictionary<string, string>(StringComparer.Ordinal))
            .OrderBy(static item => item.Key, StringComparer.Ordinal)
            .ToDictionary(static item => item.Key, static item => DisclosureFilter.SafeText(item.Value), StringComparer.Ordinal);
        JsonObject occurrenceMaterial = new()
        {
            ["id"] = id,
            ["subject"] = safeSubject,
            ["rule"] = definition.MessageKey,
            ["parameters"] = new JsonObject(safeParameters.Select(static item => KeyValuePair.Create<string, JsonNode?>(item.Key, JsonValue.Create(item.Value)))),
            ["cause"] = safeCause,
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
            occurrence,
            1,
            new[] { safeSubject },
            ProtocolIdentities.Rule(definition.MessageKey),
            definition.MessageKey,
            safeParameters,
            safeCause,
            DisclosureFilter.SafeText(consequence),
            remediations ?? Array.Empty<Remediation>(),
            Array.Empty<EvidenceReference>());
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
}
