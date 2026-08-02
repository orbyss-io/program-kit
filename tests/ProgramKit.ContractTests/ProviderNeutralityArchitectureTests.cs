using System;
using System.IO;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ProviderNeutralityArchitectureTests
{
    [TestMethod]
    public void Canonical_conformance_artifacts_contain_no_reference_provider_surface()
    {
        string[] roots =
        {
            Path.Combine(TestRepository.Root, "src", "ProgramKit.Contracts"),
            Path.Combine(TestRepository.Root, "src", "ProgramKit.SessionIntegration"),
            Path.Combine(TestRepository.Root, "tests", "Fixtures", "SessionIntegration", "Providers", "Conformance"),
        };
        foreach (string file in roots.SelectMany(static root => Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories)).Where(static file => file.EndsWith(".cs", StringComparison.Ordinal) || file.EndsWith(".json", StringComparison.Ordinal)))
        {
            string content = File.ReadAllText(file);
            Assert.IsFalse(content.Contains("Codex", StringComparison.OrdinalIgnoreCase), file);
            Assert.IsFalse(content.Contains(".agents/", StringComparison.OrdinalIgnoreCase), file);
            Assert.IsFalse(content.Contains("openai.yaml", StringComparison.OrdinalIgnoreCase), file);
        }
    }
}
