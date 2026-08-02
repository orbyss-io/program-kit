using System;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterDiagnosticTests
{
    [TestMethod]
    public void Every_public_adapter_diagnostic_has_one_definition_and_a_production_factory_trigger()
    {
        Assert.AreEqual(12, AdapterDiagnosticCatalog.Definitions.Count);
        Assert.AreEqual(12, AdapterDiagnosticCatalog.Definitions.Select(static item => item.Id).Distinct(StringComparer.Ordinal).Count());
        foreach (AdapterFailureKind kind in Enum.GetValues<AdapterFailureKind>())
        {
            Diagnostic diagnostic = AdapterDiagnosticFactory.Create(
                kind,
                AdapterDiagnosticFactory.RepositoryPath("specs/feature"),
                AdapterDiagnosticFactory.Public("valid-exact-input"),
                AdapterDiagnosticFactory.Public("boundary-refusal"));
            AdapterDiagnosticDefinition definition = AdapterDiagnosticCatalog.Get(kind);
            Assert.AreEqual(definition.Id, diagnostic.Id);
            Assert.AreEqual(definition.Disposition, diagnostic.Disposition);
            Assert.IsTrue(diagnostic.Evidence.Count > 0, diagnostic.Id);
            Assert.IsTrue(diagnostic.Remediations.Count > 0, diagnostic.Id);
            Assert.IsTrue(diagnostic.Remediations.All(static item => item.RequestArguments is { Count: > 0 } || item.RequestArtifact is not null || item.RequestDocument is not null), diagnostic.Id);
            Assert.IsFalse(string.IsNullOrWhiteSpace(diagnostic.Expected.Value), diagnostic.Id);
            Assert.IsFalse(string.IsNullOrWhiteSpace(diagnostic.Observed.Value), diagnostic.Id);
        }
    }

    [TestMethod]
    public void Diagnostic_aggregation_uses_the_strictest_typed_disposition()
    {
        Diagnostic retry = Create(AdapterFailureKind.ProcessFailure);
        Diagnostic stop = Create(AdapterFailureKind.ForbiddenOperation);
        Diagnostic revise = Create(AdapterFailureKind.InvalidHandoff);
        Assert.AreEqual(PrimaryDisposition.Stop, AdapterDiagnosticCatalog.Aggregate(new[] { retry, stop, revise }));
    }

    [TestMethod]
    public void Unknown_or_sensitive_values_are_withheld_by_construction()
    {
        SafeValue withheld = AdapterDiagnosticFactory.Withheld("unclassified-external-value");
        Assert.AreEqual(SafeValueClassification.Withheld, withheld.Classification);
        Assert.IsNull(withheld.Value);
        Assert.IsNotNull(withheld.PolicyReference);
    }

    private static Diagnostic Create(AdapterFailureKind kind) => AdapterDiagnosticFactory.Create(
        kind,
        AdapterDiagnosticFactory.Public("subject"),
        AdapterDiagnosticFactory.Public("expected"),
        AdapterDiagnosticFactory.Public("observed"));
}
