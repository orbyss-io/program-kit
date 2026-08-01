using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Diagnostics;

public sealed record ClaudeDiagnosticDefinition(
    string Id,
    string Trigger,
    string Category,
    string Severity,
    string PrimaryDisposition,
    string Expected,
    string Consequence,
    string SafeRemediation);

public static class ClaudeDiagnosticCatalog
{
    public const string Version = "1.0.0";

    public static string Id(int number) => $"program-kit.session.claude-code/PKCLD{number:0000}";

    public static IReadOnlyDictionary<string, ClaudeDiagnosticDefinition> Entries { get; } =
        new ReadOnlyDictionary<string, ClaudeDiagnosticDefinition>(new[]
        {
            Define(1, "The observed Claude Code version is missing or differs from 2.1.220.", "compatibility", "error", "select-compatible", "Exact Claude Code 2.1.220", "The selected provider support envelope is unavailable.", "Install or select the exact reviewed provider release, or select another exact adapter."),
            Define(2, "The project-skill projection loses required canonical meaning.", "conformance", "error", "stop", "A lossless project-skill projection", "The adapter cannot preserve the canonical session contract.", "Correct the adapter projection or classify the provider surface as incompatible."),
            Define(3, "Exact skill bytes exist but workspace trust or discovery is not established.", "availability", "warning", "retry", "A fresh trusted session that discovers the exact skill", "Installation may be exact while provider availability remains unknown.", "Review workspace trust as a human and start or reload the exact supported session."),
            Define(4, "Provider invocation changes executable, scope, arguments, output, or exit meaning.", "transport", "error", "stop", "An exact executable plus argument-array binding", "Program Kit result meaning cannot be trusted through this transport.", "Correct the provider binding and rerun deterministic conformance."),
            Define(5, "Provider process permission prevents the exact CLI invocation.", "authority", "error", "request-approval", "Separate bounded provider process permission", "The process did not start; Program Kit effect authority was not evaluated.", "Ask the human for bounded process permission without creating Program Kit authority."),
            Define(6, "Live review is missing, interrupted, incomplete, contradictory, or uses another provider identity.", "evidence", "warning", "review", "Complete bounded review for the exact provider identity", "Live-provider fitness remains not evaluated.", "Rerun the bounded external review or keep the support limitation explicit."),
            Define(7, "Provider-reported success conflicts with Program Kit or filesystem evidence.", "evidence", "error", "stop", "Program Kit and independent effect evidence agree", "The provider trial is invalid and cannot establish success.", "Trust Program Kit and independent effect evidence and fail the provider trial."),
            Define(8, "The isolated-machine boundary contains prohibited authoring or prior-session state.", "provenance", "error", "recreate-environment", "A clean external consumer environment", "The isolated-machine claim is invalid.", "Recreate and revalidate a clean external consumer environment."),
        }.ToDictionary(static item => item.Id, StringComparer.Ordinal));

    public static string CanonicalContent => string.Join('\n', Entries.Values.Select(static item =>
        $"{item.Id}|{item.Trigger}|{item.Category}|{item.Severity}|{item.PrimaryDisposition}|{item.Expected}|{item.Consequence}|{item.SafeRemediation}"));

    public static string Digest => Digests.Sha256(Encoding.UTF8.GetBytes(CanonicalContent));

    private static ClaudeDiagnosticDefinition Define(
        int number,
        string trigger,
        string category,
        string severity,
        string disposition,
        string expected,
        string consequence,
        string remediation) => new(Id(number), trigger, category, severity, disposition, expected, consequence, remediation);
}
