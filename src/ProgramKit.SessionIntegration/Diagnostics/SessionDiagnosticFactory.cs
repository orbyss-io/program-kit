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
        string safeSubject = DisclosureFilter.SafeLogicalValue(subject);
        string safeCause = DisclosureFilter.SafeText(cause);
        string occurrence = Digests.Sha256(Encoding.UTF8.GetBytes($"{id}\n{safeSubject}\n{safeCause}"));
        return new Diagnostic(
            id,
            ProtocolIdentities.Catalog("orbyss.program-kit.session", "integration"),
            Enum.Parse<DiagnosticSeverity>(definition.Severity, true),
            Enum.Parse<DiagnosticCategory>(definition.Category, true),
            phase,
            occurrence,
            1,
            new[] { safeSubject },
            ProtocolIdentities.Rule(definition.MessageKey),
            definition.MessageKey,
            new Dictionary<string, string>(StringComparer.Ordinal)
            {
                ["expected"] = DisclosureFilter.SafeText(definition.Expected),
                ["trigger"] = DisclosureFilter.SafeText(definition.Trigger),
            },
            safeCause,
            DisclosureFilter.SafeText(definition.Consequence),
            Array.Empty<Remediation>(),
            Array.Empty<EvidenceReference>());
    }
}
