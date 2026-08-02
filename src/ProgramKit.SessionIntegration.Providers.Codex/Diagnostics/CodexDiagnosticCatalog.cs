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
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Diagnostics;

public static class CodexDiagnosticCatalog
{
    public const string Version = "1.0.0";

    public static IReadOnlyDictionary<string, SessionDiagnosticDefinition> Entries { get; } =
        new ReadOnlyDictionary<string, SessionDiagnosticDefinition>(new Dictionary<string, SessionDiagnosticDefinition>(StringComparer.Ordinal)
        {
            [Id(1)] = Entry(1, DiagnosticSeverity.Error, DiagnosticCategory.Conformance, "codex.surface-not-supported", false, PrimaryDisposition.Stop, "The selected Codex version does not support or has not been evaluated for the exact repository-skill surface.", "The selected provider version is present in the exact adapter support envelope.", "Repository-skill discovery and result transport cannot be attributed to a supported surface.", "Select an exact Codex version evaluated by the adapter, then restart the read-only preflight."),
            [Id(2)] = Entry(2, DiagnosticSeverity.Error, DiagnosticCategory.Conformance, "codex.projection-invalid", false, PrimaryDisposition.Revise, "The projected Codex skill does not preserve the exact canonical guidance and definition binding.", "Every projected byte conforms to the exact adapter template and canonical definition.", "The session could weaken authority, result handling, or provider-neutral meaning.", "Revise the adapter or select a conforming projection; do not weaken the canonical boundary."),
            [Id(3)] = Entry(3, DiagnosticSeverity.Warning, DiagnosticCategory.External, "codex.availability-not-observed", true, PrimaryDisposition.Retry, "Exact skill bytes are installed but fresh-session discovery has not been observed.", "A fresh Codex session discovers the exact admitted skill projection.", "Installation may be exact while provider-session availability remains unknown.", "Start one fresh Codex session and repeat only the bounded discovery observation; do not reinstall."),
        });

    private static readonly JsonObject CatalogDocument = BuildDocument();

    public static GovernedIdentity Identity { get; } = new(
        "orbyss.program-kit.codex",
        "diagnostic-catalog",
        "session-provider",
        Version,
        CanonicalJson.Digest(CatalogDocument));

    public static ArtifactReference Artifact { get; } = new(
        Identity,
        "application/json",
        "artifacts/evidence/codex-diagnostic-catalog.json",
        Identity.Digest,
        ArtifactOwnership.GeneratedOwned);

    public static string Id(int number) => $"program-kit.session.codex/PKCDX{number:0000}";

    public static SessionDiagnosticDefinition Get(string id) => Entries.TryGetValue(id, out SessionDiagnosticDefinition? value) ? value : throw new KeyNotFoundException(id);

    public static JsonObject ToDocument() => (JsonObject)CatalogDocument.DeepClone();

    public static EvidenceReference EvidenceFor(string diagnosticId) => new(
        Exact("diagnostic-definition-evidence", diagnosticId.Replace('/', '-'), $"{diagnosticId}\n{Identity.Digest}"),
        Identity,
        ProtocolIdentities.Rule("diagnostic-contract"),
        Artifact,
        "current");

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
            ["category"] = SessionDiagnosticCatalog.Kebab(definition.Category),
            ["defaultSeverity"] = SessionDiagnosticCatalog.Kebab(definition.Severity),
            ["messageKey"] = definition.MessageKey,
            ["primaryDisposition"] = SessionDiagnosticCatalog.Kebab(definition.Disposition),
            ["parameterDisclosure"] = new JsonObject(),
            ["remediationKinds"] = new JsonArray(SessionDiagnosticCatalog.Kebab(definition.Disposition)),
            ["status"] = "active",
        }).ToArray()),
    };

    private static GovernedIdentity Exact(string kind, string name, string material) => new(
        "orbyss.program-kit.codex",
        kind,
        name,
        Version,
        Digests.Sha256(Encoding.UTF8.GetBytes(material)));
}
