using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public static class DiagnosticFactory
{
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
        string occurrence = Digests.Sha256(Encoding.UTF8.GetBytes($"{id}\n{safeSubject}\n{safeCause}"));
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
            parameters ?? new Dictionary<string, string>(StringComparer.Ordinal),
            safeCause,
            DisclosureFilter.SafeText(consequence),
            remediations ?? Array.Empty<Remediation>(),
            Array.Empty<EvidenceReference>());
    }

    public static DiagnosticView View(IEnumerable<Diagnostic> diagnostics)
    {
        Diagnostic[] ordered = diagnostics
            .OrderBy(static item => item.Phase)
            .ThenBy(static item => item.Category)
            .ThenByDescending(static item => item.Severity)
            .ThenBy(static item => item.Id, StringComparer.Ordinal)
            .ThenBy(static item => item.OccurrenceKey, StringComparer.Ordinal)
            .ToArray();
        string digest = Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', ordered.Select(static item => item.OccurrenceKey))));
        return new DiagnosticView(ordered.Length, ordered.Length, 0, "program-kit.diagnostic-grouping/v1", digest, ordered);
    }
}
