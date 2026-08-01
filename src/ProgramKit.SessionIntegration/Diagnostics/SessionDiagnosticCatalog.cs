using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace Orbyss.ProgramKit.SessionIntegration.Diagnostics;

public sealed record SessionDiagnosticDefinition(
    string Id,
    string Severity,
    string Category,
    string MessageKey,
    bool Retryable,
    string Disposition,
    string SafeRemediation);

public static class SessionDiagnosticCatalog
{
    public const string Version = "1";
    public const string Prefix = "orbyss.program-kit.session/PKSES";

    public static IReadOnlyDictionary<string, SessionDiagnosticDefinition> Entries { get; } =
        new ReadOnlyDictionary<string, SessionDiagnosticDefinition>(new Dictionary<string, SessionDiagnosticDefinition>(StringComparer.Ordinal)
        {
            [Id(1)] = Entry(1, "error", "request", "session.invalid-request", false, "revise", "Correct the identified request field and explain again."),
            [Id(2)] = Entry(2, "error", "resolution", "session.provider-missing", false, "provide-input", "Select one explicitly registered compatible provider."),
            [Id(3)] = Entry(3, "error", "resolution", "session.provider-incompatible", false, "revise", "Install or select the exact compatible provider revision."),
            [Id(4)] = Entry(4, "error", "policy", "session.authority-denied", false, "request-approval", "Request a grant bound to this exact request and effect."),
            [Id(5)] = Entry(5, "error", "workspace", "session.ownership-collision", false, "repair", "Move or reconcile consumer-owned material before retrying."),
            [Id(6)] = Entry(6, "error", "workspace", "session.publication-interrupted", false, "repair", "Inspect the durable journal and recover the exact transaction."),
            [Id(7)] = Entry(7, "error", "workspace", "session.projection-drift", false, "repair", "Explain a repair without adopting unrecorded bytes."),
            [Id(8)] = Entry(8, "error", "policy", "session.source-workspace-prohibited", false, "stop", "Use an isolated consumer workspace; this source checkout cannot integrate itself."),
            [Id(9)] = Entry(9, "fatal", "internal", "session.failure-boundary", false, "stop", "Preserve the result identity and stop at the bounded failure."),
        });

    public static string Id(int number) => $"{Prefix}{number:0000}";

    public static SessionDiagnosticDefinition Get(string id) => Entries.TryGetValue(id, out SessionDiagnosticDefinition? value) ? value : throw new KeyNotFoundException(id);

    private static SessionDiagnosticDefinition Entry(int number, string severity, string category, string key, bool retryable, string disposition, string remediation) =>
        new(Id(number), severity, category, key, retryable, disposition, remediation);
}
