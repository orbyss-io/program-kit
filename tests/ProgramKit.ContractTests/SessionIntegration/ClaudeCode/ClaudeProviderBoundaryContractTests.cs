using System;
using System.IO;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeProviderBoundaryContractTests
{
    [TestMethod]
    public void Provider_neutral_product_assemblies_contain_no_Claude_surface_vocabulary()
    {
        string[] roots =
        {
            Path.Combine(TestRepository.Root, "src", "ProgramKit.Contracts"),
            Path.Combine(TestRepository.Root, "src", "ProgramKit.Kernel"),
            Path.Combine(TestRepository.Root, "src", "ProgramKit.SessionIntegration"),
        };

        foreach (string root in roots)
            foreach (string file in Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories))
            {
                if (!file.EndsWith(".cs", StringComparison.Ordinal) && !file.EndsWith(".json", StringComparison.Ordinal)) continue;
                string content = File.ReadAllText(file);
                Assert.IsFalse(content.Contains("ClaudeCode", StringComparison.OrdinalIgnoreCase), file);
                Assert.IsFalse(content.Contains(".claude/", StringComparison.OrdinalIgnoreCase), file);
                Assert.IsFalse(content.Contains("PKCLD", StringComparison.Ordinal), file);
            }
    }
}
