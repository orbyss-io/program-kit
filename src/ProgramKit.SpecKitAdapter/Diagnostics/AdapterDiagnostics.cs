using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;

public enum AdapterFailureKind
{
    UnsupportedCompatibility = 1,
    InvalidConfiguration,
    UnresolvedApplicability,
    InvalidSelection,
    InvalidHandoff,
    InvalidReview,
    StaleTrace,
    UnsafePath,
    PublicationDrift,
    ProcessFailure,
    InvalidAuthority,
    ForbiddenOperation,
}

public sealed record AdapterDiagnosticDefinition(
    AdapterFailureKind Kind,
    string Id,
    DiagnosticCategory Category,
    DiagnosticSeverity Severity,
    PrimaryDisposition Disposition,
    string MessageKey);

public static class AdapterDiagnosticCatalog
{
    public const string Authority = "orbyss.program-kit.spec-kit-adapter";

    public static IReadOnlyList<AdapterDiagnosticDefinition> Definitions { get; } = new[]
    {
        Definition(AdapterFailureKind.UnsupportedCompatibility, DiagnosticCategory.Conformance, DiagnosticSeverity.Fatal, PrimaryDisposition.Stop, "compatibility.unsupported"),
        Definition(AdapterFailureKind.InvalidConfiguration, DiagnosticCategory.Workspace, DiagnosticSeverity.Error, PrimaryDisposition.ProvideInput, "config.invalid"),
        Definition(AdapterFailureKind.UnresolvedApplicability, DiagnosticCategory.Semantic, DiagnosticSeverity.Error, PrimaryDisposition.ProvideInput, "applicability.unresolved"),
        Definition(AdapterFailureKind.InvalidSelection, DiagnosticCategory.Resolution, DiagnosticSeverity.Error, PrimaryDisposition.ProvideInput, "selection.invalid"),
        Definition(AdapterFailureKind.InvalidHandoff, DiagnosticCategory.Semantic, DiagnosticSeverity.Error, PrimaryDisposition.Revise, "handoff.invalid"),
        Definition(AdapterFailureKind.InvalidReview, DiagnosticCategory.Policy, DiagnosticSeverity.Error, PrimaryDisposition.RequestApproval, "review.invalid"),
        Definition(AdapterFailureKind.StaleTrace, DiagnosticCategory.Semantic, DiagnosticSeverity.Error, PrimaryDisposition.Revise, "trace.stale"),
        Definition(AdapterFailureKind.UnsafePath, DiagnosticCategory.Workspace, DiagnosticSeverity.Fatal, PrimaryDisposition.Stop, "path.unsafe"),
        Definition(AdapterFailureKind.PublicationDrift, DiagnosticCategory.Workspace, DiagnosticSeverity.Error, PrimaryDisposition.Repair, "publication.drift"),
        Definition(AdapterFailureKind.ProcessFailure, DiagnosticCategory.External, DiagnosticSeverity.Error, PrimaryDisposition.Retry, "process.failed"),
        Definition(AdapterFailureKind.InvalidAuthority, DiagnosticCategory.Policy, DiagnosticSeverity.Error, PrimaryDisposition.RequestApproval, "authority.invalid"),
        Definition(AdapterFailureKind.ForbiddenOperation, DiagnosticCategory.Policy, DiagnosticSeverity.Fatal, PrimaryDisposition.Stop, "operation.forbidden"),
    };

    public static JsonObject Document { get; } = LoadDocument();

    public static string Digest { get; } = CanonicalDocument.Digest(Document);

    public static GovernedIdentity Identity { get; } = new(Authority, "diagnostic-catalog", "spec-kit-adapter", "1.0.0", Digest);

    public static AdapterDiagnosticDefinition Get(AdapterFailureKind kind) => Definitions.Single(item => item.Kind == kind);

    public static PrimaryDisposition Aggregate(IEnumerable<Diagnostic> diagnostics) => diagnostics
        .Select(static item => item.Disposition)
        .OrderByDescending(Strictness)
        .FirstOrDefault(PrimaryDisposition.Complete);

    private static AdapterDiagnosticDefinition Definition(
        AdapterFailureKind kind,
        DiagnosticCategory category,
        DiagnosticSeverity severity,
        PrimaryDisposition disposition,
        string key) => new(kind, $"{Authority}/PKSKA{(int)kind:D4}", category, severity, disposition, $"adapter.{key}");

    private static int Strictness(PrimaryDisposition disposition) => disposition switch
    {
        PrimaryDisposition.Stop => 7,
        PrimaryDisposition.Repair => 6,
        PrimaryDisposition.RequestApproval => 5,
        PrimaryDisposition.Revise => 4,
        PrimaryDisposition.ProvideInput => 3,
        PrimaryDisposition.Retry => 2,
        _ => 1,
    };

    private static JsonObject LoadDocument()
    {
        Assembly assembly = typeof(AdapterDiagnosticCatalog).Assembly;
        string name = assembly.GetManifestResourceNames().Single(resource => resource.EndsWith("Resources.diagnostic-catalog.json", StringComparison.Ordinal));
        using System.IO.Stream stream = assembly.GetManifestResourceStream(name) ?? throw new InvalidOperationException("The adapter diagnostic catalog resource is missing.");
        using System.IO.MemoryStream buffer = new();
        stream.CopyTo(buffer);
        JsonObject document = CanonicalDocument.Parse(buffer.ToArray()).AsObject();
        AdapterSchemaValidator.Validate("diagnostic-catalog.schema.json", document);
        JsonObject[] declared = document["definitions"]!.AsArray().OfType<JsonObject>().ToArray();
        if (declared.Length != Definitions.Count) throw new InvalidOperationException("The adapter diagnostic catalog definition count differs.");
        for (int index = 0; index < declared.Length; index++)
        {
            AdapterDiagnosticDefinition typed = Definitions[index];
            if (declared[index]["id"]!.GetValue<string>() != typed.Id
                || declared[index]["category"]!.GetValue<string>() != Kebab(typed.Category)
                || declared[index]["severity"]!.GetValue<string>() != Kebab(typed.Severity)
                || declared[index]["disposition"]!.GetValue<string>() != Kebab(typed.Disposition)
                || declared[index]["messageKey"]!.GetValue<string>() != typed.MessageKey)
                throw new InvalidOperationException("The adapter diagnostic catalog resource and typed definitions differ.");
        }
        return document;
    }

    private static string Kebab<T>(T value) where T : struct, Enum
    {
        string name = value.ToString();
        StringBuilder result = new();
        for (int index = 0; index < name.Length; index++)
        {
            if (index > 0 && char.IsUpper(name[index])) result.Append('-');
            result.Append(char.ToLowerInvariant(name[index]));
        }

        return result.ToString();
    }
}

public static class AdapterDiagnosticFactory
{
    public static Diagnostic Create(AdapterFailureKind kind, SafeValue subject, SafeValue expected, SafeValue observed)
    {
        AdapterDiagnosticDefinition definition = AdapterDiagnosticCatalog.Get(kind);
        subject = DisclosureFilter.Enforce(subject);
        expected = DisclosureFilter.Enforce(expected);
        observed = DisclosureFilter.Enforce(observed);
        GovernedIdentity catalog = AdapterDiagnosticCatalog.Identity;
        ArtifactReference catalogArtifact = new(catalog, "application/json", "diagnostic-catalog.json", AdapterDiagnosticCatalog.Digest, ArtifactOwnership.GeneratedOwned);
        EvidenceReference definitionEvidence = new(
            Identity("evidence", $"definition-{(int)kind:D4}", "1.0.0"),
            ProtocolIdentities.Rule(definition.MessageKey),
            catalog,
            catalogArtifact,
            "current");
        return new Diagnostic(
            definition.Id,
            catalog,
            definition.Severity,
            definition.Category,
            OperationPhase.Validation,
            definition.Disposition,
            $"{definition.Id}:1",
            1,
            new[] { subject.Value ?? "withheld" },
            ProtocolIdentities.Rule(definition.MessageKey),
            definition.MessageKey,
            new Dictionary<string, SafeValue>(StringComparer.Ordinal) { ["subject"] = subject },
            Public("adapter-boundary-refusal"),
            Public("requested-operation-not-admitted"),
            expected,
            observed,
            new[]
            {
                new Remediation("submit-corrected-request", Array.Empty<string>(), Array.Empty<string>(), RequestedEffect.None, Array.Empty<string>(), null, null, new[] { "doctor", "--request", "requests/adapter.json" }, new[] { "request-validates" }, OperationPhase.Request),
            },
            new[] { definitionEvidence });
    }

    public static SafeValue Public(string value) => DisclosureFilter.PublicText(value);

    public static SafeValue RepositoryPath(string value) => DisclosureFilter.RepositoryPath(value);

    public static SafeValue Withheld(string reason) => DisclosureFilter.External(reason);

    private static GovernedIdentity Identity(string kind, string name, string revision)
    {
        string material = $"{AdapterDiagnosticCatalog.Authority}\n{kind}\n{name}\n{revision}";
        string digest = "sha256:" + Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(material))).ToLowerInvariant();
        return new GovernedIdentity(AdapterDiagnosticCatalog.Authority, kind, name, revision, digest);
    }
}
