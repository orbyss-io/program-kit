using System;
using System.Collections.Generic;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

namespace Orbyss.ProgramKit.SessionIntegration.Definitions;

public sealed record InvocationTransportCase(
    string Kind,
    string DiagnosticId,
    bool FabricateOperationResult,
    bool LaunchProvider,
    string SafeNextAction);

public static class InvocationTransportGuidance
{
    public static IReadOnlyList<InvocationTransportCase> Cases { get; } = new[]
    {
        Case("cli-unavailable", "Make the exact reviewed CLI executable available, then retry the read-only preflight."),
        Case("shell-timeout", "Bound the invocation and retry the read-only preflight after the channel is responsive."),
        Case("nonzero-without-envelope", "Preserve the exit evidence and retry only after the CLI can return one complete envelope."),
        Case("malformed-json", "Preserve the malformed bytes as external evidence and correct the invocation channel."),
        Case("missing-result", "Treat the channel as inconclusive and retry the read-only preflight."),
    };

    public static InvocationTransportCase Get(string kind)
    {
        foreach (InvocationTransportCase item in Cases)
        {
            if (string.Equals(item.Kind, kind, StringComparison.Ordinal)) return item;
        }

        throw new KeyNotFoundException(kind);
    }

    private static InvocationTransportCase Case(string kind, string action) =>
        new(kind, SessionDiagnosticCatalog.Id(7), false, false, action);
}
