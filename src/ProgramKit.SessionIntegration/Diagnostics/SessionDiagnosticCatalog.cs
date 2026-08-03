using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.SessionIntegration.Diagnostics;

public sealed record SessionDiagnosticDefinition(
    string Id,
    DiagnosticSeverity Severity,
    DiagnosticCategory Category,
    string MessageKey,
    string Trigger,
    string Expected,
    string Consequence,
    bool Retryable,
    PrimaryDisposition Disposition,
    string SafeRemediation);

public static class SessionDiagnosticCatalog
{
    public const string Version = "1.0.0";
    public const string Prefix = "program-kit.session/PKSES";

    public static IReadOnlyDictionary<string, SessionDiagnosticDefinition> Entries { get; } =
        new ReadOnlyDictionary<string, SessionDiagnosticDefinition>(new Dictionary<string, SessionDiagnosticDefinition>(StringComparer.Ordinal)
        {
            [Id(1)] = Entry(1, DiagnosticSeverity.Error, DiagnosticCategory.Conformance, "session.cli-mismatch", false, PrimaryDisposition.Stop, "The selected CLI release identity does not match the invoked package, executable, command, runtime, or reported version.", "Every CLI release field matches exact observed evidence.", "CLI results cannot be attributed to the selected release.", "Select or install the exact reviewed CLI release, then explain again."),
            [Id(2)] = Entry(2, DiagnosticSeverity.Error, DiagnosticCategory.Resolution, "session.provider-missing", false, PrimaryDisposition.ProvideInput, "The exact provider, adapter, definition, or conformance profile is unavailable.", "One explicitly registered compatible provider selection is present.", "No provider projection can be trusted.", "Select one exact registered provider and compatible revision."),
            [Id(3)] = Entry(3, DiagnosticSeverity.Error, DiagnosticCategory.Conformance, "session.provider-incompatible", false, PrimaryDisposition.Revise, "The selected provider cannot preserve a mandatory operation, authority, effect, result, disclosure, or scope boundary.", "The provider passes the exact conformance profile.", "The provider projection would weaken the canonical contract.", "Revise the provider selection or install a conforming adapter; do not weaken the boundary."),
            [Id(4)] = Entry(4, DiagnosticSeverity.Error, DiagnosticCategory.Workspace, "session.projection-drift", false, PrimaryDisposition.Repair, "An admitted projection, definition, adapter, or CLI binding differs from current state.", "Every admitted binding and generated-owned byte remains exact.", "Verification and removal cannot trust current live state.", "Explain a separate bounded repair request; do not adopt or overwrite current bytes."),
            [Id(5)] = Entry(5, DiagnosticSeverity.Error, DiagnosticCategory.Workspace, "session.publication-interrupted", false, PrimaryDisposition.Repair, "Publication or removal began but complete trusted live state cannot be proven.", "The durable journal and every live operation prove one completed transaction.", "Effect state may be partial or indeterminate and blind retry is unsafe.", "Inspect the exact journal and recover or roll back the recorded transaction before retrying."),
            [Id(6)] = Entry(6, DiagnosticSeverity.Error, DiagnosticCategory.Policy, "session.source-workspace-prohibited", false, PrimaryDisposition.Stop, "A consumer lifecycle operation targeted the Program Kit source-authoring repository.", "Consumer session integration runs only in an isolated consumer workspace.", "Self-integration could rewrite the source rules governing the active session.", "Stop and use a separate consumer workspace; no force or waiver exists."),
            [Id(7)] = Entry(7, DiagnosticSeverity.Error, DiagnosticCategory.External, "session.transport-failure", true, PrimaryDisposition.Retry, "The invocation channel failed before a valid Program Kit result was preserved.", "One complete current operation-result document is obtained without provider rewriting.", "No Program Kit outcome or effect can be inferred.", "Retry only the read-only transport preflight after correcting the classified channel failure."),
            [Id(8)] = Entry(8, DiagnosticSeverity.Error, DiagnosticCategory.Workspace, "session.installation-missing", false, PrimaryDisposition.ProvideInput, "Verification or removal requires an exact admitted installation record that is absent.", "One current installation record binds the selected provider and workspace.", "Installed ownership, exactness, and safe removal cannot be proven.", "Install through an authorized request or provide the exact admitted record; do not adopt ambient files."),
            [Id(9)] = Entry(9, DiagnosticSeverity.Warning, DiagnosticCategory.Conformance, "session.availability-not-evaluated", true, PrimaryDisposition.Retry, "Exact projection bytes exist but fresh provider-session discovery has not been established.", "A separately observed fresh session discovers the exact admitted projection.", "Installation can be exact while current-session availability remains unknown.", "Start a fresh provider session and rerun read-only verification; do not reinstall."),
        });

    private static readonly JsonObject CatalogDocument = BuildDocument();

    public static GovernedIdentity Identity { get; } = new(
        "orbyss.program-kit.session",
        "diagnostic-catalog",
        "session",
        Version,
        CanonicalJson.Digest(CatalogDocument));

    public static ArtifactReference Artifact { get; } = new(
        Identity,
        "application/json",
        "artifacts/evidence/session-diagnostic-catalog.json",
        Identity.Digest,
        ArtifactOwnership.GeneratedOwned);

    public static string Id(int number) => $"{Prefix}{number:0000}";

    public static SessionDiagnosticDefinition Get(string id) => Entries.TryGetValue(id, out SessionDiagnosticDefinition? value) ? value : throw new KeyNotFoundException(id);

    public static JsonObject ToDocument() => (JsonObject)CatalogDocument.DeepClone();

    public static EvidenceReference EvidenceFor(string diagnosticId) => new(
        Exact("orbyss.program-kit.session", "diagnostic-definition-evidence", diagnosticId.Replace('/', '-'), Version, $"{diagnosticId}\n{Identity.Digest}"),
        Identity,
        ProtocolIdentities.Rule("diagnostic-contract"),
        Artifact,
        "current");

    public static string Kebab<T>(T value) where T : struct, Enum =>
        string.Concat(value.ToString().Select((character, index) => index > 0 && char.IsUpper(character)
            ? $"-{char.ToLowerInvariant(character)}"
            : char.ToLowerInvariant(character).ToString()));

    private static SessionDiagnosticDefinition Entry(int number, DiagnosticSeverity severity, DiagnosticCategory category, string key, bool retryable, PrimaryDisposition disposition, string trigger, string expected, string consequence, string remediation) =>
        new(Id(number), severity, category, key, trigger, expected, consequence, retryable, disposition, remediation);

    private static JsonObject BuildDocument() => new()
    {
        ["schema"] = "program-kit.diagnostic-catalog/v1",
        ["canonicalProfile"] = CanonicalJson.Profile,
        ["protocolRevision"] = Version,
        ["entries"] = new JsonArray(Entries.Values.OrderBy(static item => item.Id, StringComparer.Ordinal).Select(static definition => new JsonObject
        {
            ["id"] = definition.Id,
            ["trigger"] = definition.Trigger,
            ["violatedInvariant"] = definition.Expected,
            ["category"] = Kebab(definition.Category),
            ["defaultSeverity"] = Kebab(definition.Severity),
            ["messageKey"] = definition.MessageKey,
            ["primaryDisposition"] = Kebab(definition.Disposition),
            ["parameterDisclosure"] = new JsonObject(),
            ["remediationKinds"] = new JsonArray(Kebab(definition.Disposition)),
            ["status"] = "active",
        }).ToArray()),
    };

    private static GovernedIdentity Exact(string authority, string kind, string name, string revision, string material) => new(
        authority,
        kind,
        name,
        revision,
        Digests.Sha256(Encoding.UTF8.GetBytes(material)));
}
