using System;
using System.Collections.Generic;
using System.Text;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Diagnostics;

public static class CodexDiagnosticFactory
{
    public static Diagnostic Create(string id, OperationPhase phase, string subject, string cause)
    {
        SessionDiagnosticDefinition definition = CodexDiagnosticCatalog.Get(id);
        SafeValue safeSubjectValue = DisclosureFilter.RepositoryRelative(subject);
        SafeValue safeCause = DisclosureFilter.PublicText(cause);
        SafeValue expected = DisclosureFilter.PublicText(definition.Expected);
        SafeValue consequence = DisclosureFilter.PublicText(definition.Consequence);
        string safeSubject = safeSubjectValue.Value ?? "withheld";
        string occurrence = Digests.Sha256(Encoding.UTF8.GetBytes($"{id}\n{safeSubject}\n{safeCause.Value ?? "withheld"}"));
        return new Diagnostic(
            id,
            CodexDiagnosticCatalog.Identity,
            definition.Severity,
            definition.Category,
            phase,
            definition.Disposition,
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
                    SessionDiagnosticCatalog.Kebab(definition.Disposition),
                    new[] { safeSubject },
                    new[] { "diagnostic-is-current" },
                    RequestedEffect.None,
                    Array.Empty<string>(),
                    null,
                    null,
                    new[] { "help" },
                    new[] { "provider-invariant-is-re-evaluated" },
                    phase),
            },
            new[] { CodexDiagnosticCatalog.EvidenceFor(id) });
    }
}
