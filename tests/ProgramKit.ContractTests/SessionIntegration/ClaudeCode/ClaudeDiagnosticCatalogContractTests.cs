using System;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Diagnostics;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeDiagnosticCatalogContractTests
{
    [TestMethod]
    public void Catalog_contains_eight_stable_safe_actionable_provider_diagnostics()
    {
        StringAssert.Matches(ClaudeDiagnosticCatalog.Version, new("^1\\.0\\.0$"));
        Assert.AreEqual(8, ClaudeDiagnosticCatalog.Entries.Count);
        CollectionAssert.AreEqual(Enumerable.Range(1, 8).Select(ClaudeDiagnosticCatalog.Id).ToArray(), ClaudeDiagnosticCatalog.Entries.Keys.ToArray());
        Assert.AreEqual("sha256:01c390a82039bed04a5f6c38bb606eccfd2d623f84c5dd7c309a7cc5f0c7a6aa", ClaudeDiagnosticCatalog.Digest);
        foreach (ClaudeDiagnosticDefinition entry in ClaudeDiagnosticCatalog.Entries.Values)
        {
            StringAssert.StartsWith(entry.Id, "program-kit.session.claude-code/PKCLD");
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Trigger));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Expected));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Consequence));
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.SafeRemediation));
            Assert.IsFalse(entry.SafeRemediation.Contains("claude ", StringComparison.OrdinalIgnoreCase));
        }
    }
}
