using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;

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
}

public static class AdapterDiagnosticFactory
{
    private static readonly GovernedIdentity Catalog = Identity("diagnostic-catalog", "spec-kit-adapter", "1.0.0");
    private static readonly GovernedIdentity DisclosurePolicy = Identity("policy", "safe-disclosure", "1.0.0");

    public static Diagnostic Create(AdapterFailureKind kind, SafeValue subject, SafeValue expected, SafeValue observed)
    {
        AdapterDiagnosticDefinition definition = AdapterDiagnosticCatalog.Get(kind);
        ArtifactReference catalogArtifact = new(Catalog, "application/json", "diagnostic-catalog.json", Catalog.Digest, ArtifactOwnership.GeneratedOwned);
        EvidenceReference definitionEvidence = new(
            Identity("evidence", $"definition-{(int)kind:D4}", "1.0.0"),
            ProtocolIdentities.Rule(definition.MessageKey),
            Catalog,
            catalogArtifact,
            "current");
        return new Diagnostic(
            definition.Id,
            Catalog,
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

    public static SafeValue Public(string value) => new(SafeValueClassification.Public, SafeValueKind.Text, value);

    public static SafeValue RepositoryPath(string value) => new(SafeValueClassification.RepositoryRelative, SafeValueKind.LogicalPath, value);

    public static SafeValue Withheld(string reason) => new(SafeValueClassification.Withheld, SafeValueKind.Redacted, null, reason, DisclosurePolicy);

    private static GovernedIdentity Identity(string kind, string name, string revision)
    {
        string material = $"{AdapterDiagnosticCatalog.Authority}\n{kind}\n{name}\n{revision}";
        string digest = "sha256:" + Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(material))).ToLowerInvariant();
        return new GovernedIdentity(AdapterDiagnosticCatalog.Authority, kind, name, revision, digest);
    }
}
