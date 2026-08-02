using System;
using System.Collections.Generic;
using System.Text;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;

namespace Orbyss.ProgramKit.SessionIntegration.Diagnostics;

public static class SessionDiagnosticFactory
{
    public static Diagnostic Create(string id, OperationPhase phase, string subject, string cause)
    {
        SessionDiagnosticDefinition definition = SessionDiagnosticCatalog.Get(id);
        SafeValue safeSubjectValue = DisclosureFilter.RepositoryRelative(subject);
        SafeValue safeCause = DisclosureFilter.PublicText(cause);
        SafeValue expected = DisclosureFilter.PublicText(definition.Expected);
        SafeValue consequence = DisclosureFilter.PublicText(definition.Consequence);
        string safeSubject = safeSubjectValue.Value ?? "withheld";
        string occurrence = Digests.Sha256(Encoding.UTF8.GetBytes($"{id}\n{safeSubject}\n{safeCause.Value ?? "withheld"}"));
        PrimaryDisposition disposition = definition.Disposition;
        return new Diagnostic(
            id,
            SessionDiagnosticCatalog.Identity,
            definition.Severity,
            definition.Category,
            phase,
            disposition,
            occurrence,
            1,
            new[] { safeSubject },
            ProtocolIdentities.Rule(definition.MessageKey),
            definition.MessageKey,
            new Dictionary<string, SafeValue>(StringComparer.Ordinal)
            {
                ["expected"] = expected,
                ["trigger"] = DisclosureFilter.PublicText(definition.Trigger),
            },
            safeCause,
            consequence,
            expected,
            safeCause,
            new[]
            {
                new Remediation(
                    RemediationKind(disposition),
                    new[] { safeSubject },
                    new[] { "diagnostic-is-current" },
                    RequestedEffect.None,
                    Array.Empty<string>(),
                    null,
                    null,
                    new[] { "help" },
                    new[] { "session-invariant-is-re-evaluated" },
                    phase),
            },
            new[] { SessionDiagnosticCatalog.EvidenceFor(id) });
    }

    private static string RemediationKind(PrimaryDisposition disposition) => disposition switch
    {
        PrimaryDisposition.ProvideInput => "provide-input",
        PrimaryDisposition.Repair => "repair",
        PrimaryDisposition.Retry => "retry",
        PrimaryDisposition.Revise => "revise",
        _ => "stop",
    };
}
