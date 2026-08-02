using System;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Diagnostics;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionDiagnosticCatalogContractTests
{
    [TestMethod]
    public void Neutral_and_provider_catalogs_are_complete_unique_ordered_and_actionable()
    {
        Assert.IsTrue(string.Equals("1.0.0", SessionDiagnosticCatalog.Version, StringComparison.Ordinal));
        Assert.AreEqual(9, SessionDiagnosticCatalog.Entries.Count);
        CollectionAssert.AreEqual(Enumerable.Range(1, 9).Select(SessionDiagnosticCatalog.Id).ToArray(), SessionDiagnosticCatalog.Entries.Keys.ToArray());
        foreach (SessionDiagnosticDefinition entry in SessionDiagnosticCatalog.Entries.Values)
        {
            StringAssert.StartsWith(entry.Id, "program-kit.session/PKSES");
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Trigger));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Expected));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Consequence));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.SafeRemediation));
            Assert.IsTrue(entry.SafeRemediation.Length <= 300);
        }

        CollectionAssert.AreEqual(new[] { "program-kit.session.codex/PKCDX0001", "program-kit.session.codex/PKCDX0002", "program-kit.session.codex/PKCDX0003" }, CodexDiagnosticCatalog.Entries.Keys.ToArray());
        foreach (SessionDiagnosticDefinition entry in CodexDiagnosticCatalog.Entries.Values)
        {
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Trigger));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Expected));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Consequence));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.SafeRemediation));
        }
        Assert.AreEqual(SessionDiagnosticCatalog.Identity.Digest, SessionDiagnosticCatalog.Artifact.Digest);
        Assert.AreEqual(CodexDiagnosticCatalog.Identity.Digest, CodexDiagnosticCatalog.Artifact.Digest);
        ContractAssertions.AssertValid(ContractAssertions.OperationResult, SessionDiagnosticCatalog.ToDocument());
        ContractAssertions.AssertValid(ContractAssertions.OperationResult, CodexDiagnosticCatalog.ToDocument());
    }
}
