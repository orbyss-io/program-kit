using System;
using System.IO;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionRuntimeIsolationAcceptanceTests
{
    [TestMethod]
    public void Session_projection_is_development_only_and_never_enters_generated_runtime_projects()
    {
        string templates = string.Join('\n', Directory.EnumerateFiles(Path.Combine(TestRepository.Root, "src", "ProgramKit.Providers.DotNet"), "*.cs", SearchOption.AllDirectories).Select(File.ReadAllText));
        Assert.IsFalse(templates.Contains("ProgramKit.SessionIntegration", StringComparison.Ordinal));
        Assert.IsFalse(templates.Contains("program-kit/skill", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(templates.Contains("Codex", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(templates.Contains("SpecKit", StringComparison.OrdinalIgnoreCase));
    }
}
