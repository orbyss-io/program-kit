using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Diagnostics;

public sealed record ClaudeDiagnosticObservation(
    ClaudeDiagnosticDefinition Definition,
    string Subject,
    IReadOnlyDictionary<string, string> SafeObserved,
    string EffectState);

public static class ClaudeDiagnosticFactory
{
    public static ClaudeDiagnosticObservation Create(int number, string subject, string safeObservedValue, string effectState)
    {
        if (!ClaudeDiagnosticCatalog.Entries.TryGetValue(ClaudeDiagnosticCatalog.Id(number), out ClaudeDiagnosticDefinition? definition))
            throw new ArgumentOutOfRangeException(nameof(number));
        if (string.IsNullOrWhiteSpace(subject) || string.IsNullOrWhiteSpace(effectState))
            throw new ArgumentException("Diagnostic subject and effect state are required.");
        IReadOnlyDictionary<string, string> observed = new ReadOnlyDictionary<string, string>(
            new Dictionary<string, string>(StringComparer.Ordinal) { ["value"] = safeObservedValue });
        return new(definition, subject, observed, effectState);
    }
}
