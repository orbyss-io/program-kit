using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace Orbyss.ProgramKit.SessionIntegration.Diagnostics;

public sealed record SessionDiagnosticDefinition(
    string Id,
    string Severity,
    string Category,
    string MessageKey,
    string Trigger,
    string Expected,
    string Consequence,
    bool Retryable,
    string Disposition,
    string SafeRemediation);

public static class SessionDiagnosticCatalog
{
    public const string Version = "1.0.0";
    public const string Prefix = "program-kit.session/PKSES";

    public static IReadOnlyDictionary<string, SessionDiagnosticDefinition> Entries { get; } =
        new ReadOnlyDictionary<string, SessionDiagnosticDefinition>(new Dictionary<string, SessionDiagnosticDefinition>(StringComparer.Ordinal)
        {
            [Id(1)] = Entry(1, "error", "conformance", "session.cli-mismatch", false, "stop", "The selected CLI release identity does not match the invoked package, executable, command, runtime, or reported version.", "Every CLI release field matches exact observed evidence.", "CLI results cannot be attributed to the selected release.", "Select or install the exact reviewed CLI release, then explain again."),
            [Id(2)] = Entry(2, "error", "resolution", "session.provider-missing", false, "provide-input", "The exact provider, adapter, definition, or conformance profile is unavailable.", "One explicitly registered compatible provider selection is present.", "No provider projection can be trusted.", "Select one exact registered provider and compatible revision."),
            [Id(3)] = Entry(3, "error", "conformance", "session.provider-incompatible", false, "revise", "The selected provider cannot preserve a mandatory operation, authority, effect, result, disclosure, or scope boundary.", "The provider passes the exact conformance profile.", "The provider projection would weaken the canonical contract.", "Revise the provider selection or install a conforming adapter; do not weaken the boundary."),
            [Id(4)] = Entry(4, "error", "workspace", "session.projection-drift", false, "repair", "An admitted projection, definition, adapter, or CLI binding differs from current state.", "Every admitted binding and generated-owned byte remains exact.", "Verification and removal cannot trust current live state.", "Explain a separate bounded repair request; do not adopt or overwrite current bytes."),
            [Id(5)] = Entry(5, "error", "workspace", "session.publication-interrupted", false, "repair", "Publication or removal began but complete trusted live state cannot be proven.", "The durable journal and every live operation prove one completed transaction.", "Effect state may be partial or indeterminate and blind retry is unsafe.", "Inspect the exact journal and recover or roll back the recorded transaction before retrying."),
            [Id(6)] = Entry(6, "error", "policy", "session.source-workspace-prohibited", false, "stop", "A consumer lifecycle operation targeted the Program Kit source-authoring repository.", "Consumer session integration runs only in an isolated consumer workspace.", "Self-integration could rewrite the source rules governing the active session.", "Stop and use a separate consumer workspace; no force or waiver exists."),
            [Id(7)] = Entry(7, "error", "external", "session.transport-failure", true, "retry", "The invocation channel failed before a valid Program Kit result was preserved.", "One complete operation-result/v1 document is obtained without provider rewriting.", "No Program Kit outcome or effect can be inferred.", "Retry only the read-only transport preflight after correcting the classified channel failure."),
            [Id(8)] = Entry(8, "error", "workspace", "session.installation-missing", false, "provide-input", "Verification or removal requires an exact admitted installation record that is absent.", "One current installation record binds the selected provider and workspace.", "Installed ownership, exactness, and safe removal cannot be proven.", "Install through an authorized request or provide the exact admitted record; do not adopt ambient files."),
            [Id(9)] = Entry(9, "warning", "conformance", "session.availability-not-evaluated", true, "retry", "Exact projection bytes exist but fresh provider-session discovery has not been established.", "A separately observed fresh session discovers the exact admitted projection.", "Installation can be exact while current-session availability remains unknown.", "Start a fresh provider session and rerun read-only verification; do not reinstall."),
        });

    public static string Id(int number) => $"{Prefix}{number:0000}";

    public static SessionDiagnosticDefinition Get(string id) => Entries.TryGetValue(id, out SessionDiagnosticDefinition? value) ? value : throw new KeyNotFoundException(id);

    private static SessionDiagnosticDefinition Entry(int number, string severity, string category, string key, bool retryable, string disposition, string trigger, string expected, string consequence, string remediation) =>
        new(Id(number), severity, category, key, trigger, expected, consequence, retryable, disposition, remediation);
}
