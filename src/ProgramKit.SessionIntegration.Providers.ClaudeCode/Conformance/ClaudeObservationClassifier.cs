using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Manifest;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

public sealed record ClaudeObservationInput(
    string? ReportedVersion,
    ClaudeAuthenticationState AuthenticationState,
    ClaudeWorkspaceTrustState WorkspaceTrustState,
    ClaudeSkillDiscoveryState SkillDiscoveryState,
    bool InvocationPreserved,
    bool ProviderClaimsSuccess,
    OperationOutcome ProgramKitOutcome,
    bool IsolatedBoundaryClean,
    bool LiveEvidenceComplete);

public sealed record ClaudeObservationClassification(
    string Availability,
    IReadOnlyList<string> DiagnosticIds,
    IReadOnlyDictionary<string, string> SafeFields);

public static class ClaudeObservationClassifier
{
    public static ClaudeObservationClassification Classify(ClaudeObservationInput input)
    {
        List<string> diagnostics = new();
        string availability;
        if (input.ReportedVersion is null)
        {
            availability = "not-evaluated";
            diagnostics.Add(ClaudeDiagnosticCatalog.Id(6));
        }
        else if (!string.Equals(input.ReportedVersion, ClaudeProviderIdentities.ProviderVersion, StringComparison.Ordinal))
        {
            availability = "unavailable";
            diagnostics.Add(ClaudeDiagnosticCatalog.Id(1));
        }
        else
        {
            availability = input.SkillDiscoveryState switch
            {
                ClaudeSkillDiscoveryState.Available => "available",
                ClaudeSkillDiscoveryState.ReloadRequired => "reload-required",
                ClaudeSkillDiscoveryState.Unavailable => "unavailable",
                _ => "not-evaluated",
            };
            if (input.SkillDiscoveryState == ClaudeSkillDiscoveryState.ReloadRequired ||
                input.WorkspaceTrustState == ClaudeWorkspaceTrustState.Required)
                diagnostics.Add(ClaudeDiagnosticCatalog.Id(3));
            else if (input.SkillDiscoveryState == ClaudeSkillDiscoveryState.NotEvaluated && !input.LiveEvidenceComplete)
                diagnostics.Add(ClaudeDiagnosticCatalog.Id(6));
        }

        if (!input.InvocationPreserved) diagnostics.Add(ClaudeDiagnosticCatalog.Id(4));
        if (input.ProviderClaimsSuccess && input.ProgramKitOutcome != OperationOutcome.Succeeded) diagnostics.Add(ClaudeDiagnosticCatalog.Id(7));
        if (!input.IsolatedBoundaryClean) diagnostics.Add(ClaudeDiagnosticCatalog.Id(8));

        IReadOnlyDictionary<string, string> safeFields = new ReadOnlyDictionary<string, string>(new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["reportedVersion"] = input.ReportedVersion ?? "not-evaluated",
            ["authenticationState"] = Kebab(input.AuthenticationState),
            ["workspaceTrustState"] = Kebab(input.WorkspaceTrustState),
            ["skillDiscoveryState"] = Kebab(input.SkillDiscoveryState),
            ["programKitOutcome"] = Kebab(input.ProgramKitOutcome),
        });
        return new(availability, diagnostics.Distinct(StringComparer.Ordinal).OrderBy(static value => value, StringComparer.Ordinal).ToArray(), safeFields);
    }

    private static string Kebab<T>(T value) where T : struct, Enum => string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character) ? $"-{char.ToLowerInvariant(character)}" : char.ToLowerInvariant(character).ToString()));
}
