using System;
using System.IO;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeRuntimeIsolationAcceptanceTests
{
    [TestMethod]
    public void Reference_runtime_projects_have_no_session_or_provider_project_reference()
    {
        string templates = string.Join('\n', Directory.EnumerateFiles(Path.Combine(TestRepository.Root, "src", "ProgramKit.Providers.DotNet"), "*.cs", SearchOption.AllDirectories).Select(File.ReadAllText));
        Assert.IsGreaterThan(0, templates.Length);
        Assert.IsFalse(templates.Contains("ProgramKit.SessionIntegration", StringComparison.Ordinal));
        Assert.IsFalse(templates.Contains("ProgramKit.SessionIntegration.Providers.ClaudeCode", StringComparison.Ordinal));
        Assert.IsFalse(templates.Contains(".claude/skills", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(templates.Contains("Claude Code", StringComparison.OrdinalIgnoreCase));
    }
}
