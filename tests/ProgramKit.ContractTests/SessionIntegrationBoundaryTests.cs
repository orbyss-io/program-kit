using System;
using System.IO;
using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionIntegrationBoundaryTests
{
    [TestMethod]
    public void Canonical_contracts_and_neutral_session_assembly_have_no_provider_symbols()
    {
        foreach (string root in new[] { Path.Combine(TestRepository.Root, "src", "ProgramKit.Contracts"), Path.Combine(TestRepository.Root, "src", "ProgramKit.SessionIntegration") })
            foreach (string path in Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories).Where(static path => path.EndsWith(".cs", StringComparison.Ordinal) || path.EndsWith(".json", StringComparison.Ordinal)))
            {
                string text = File.ReadAllText(path);
                Assert.IsFalse(text.Contains(".agents/", StringComparison.OrdinalIgnoreCase), path);
                Assert.IsFalse(text.Contains("Codex", StringComparison.OrdinalIgnoreCase), path);
            }
    }

    [TestMethod]
    public void Runtime_projects_do_not_reference_session_integration_or_ai_providers()
    {
        foreach (string project in Directory.EnumerateFiles(Path.Combine(TestRepository.Root, "src"), "*.csproj", SearchOption.AllDirectories))
        {
            if (project.Contains("SessionIntegration", StringComparison.OrdinalIgnoreCase) || project.Contains("ProgramKit.Cli", StringComparison.OrdinalIgnoreCase)) continue;
            string text = File.ReadAllText(project);
            Assert.IsFalse(text.Contains("SessionIntegration", StringComparison.OrdinalIgnoreCase), project);
            Assert.IsFalse(text.Contains("OpenAI", StringComparison.OrdinalIgnoreCase), project);
        }
    }

    [TestMethod]
    public void Production_session_code_has_no_process_launch_telemetry_or_dynamic_discovery()
    {
        foreach (string root in new[] { Path.Combine(TestRepository.Root, "src", "ProgramKit.SessionIntegration"), Path.Combine(TestRepository.Root, "src", "ProgramKit.SessionIntegration.Providers.Codex") })
            foreach (string path in Directory.EnumerateFiles(root, "*.cs", SearchOption.AllDirectories))
            {
                string text = File.ReadAllText(path);
                Assert.IsFalse(text.Contains("Process.Start", StringComparison.Ordinal), path);
                Assert.IsFalse(text.Contains("Assembly.Load", StringComparison.Ordinal), path);
                Assert.IsFalse(text.Contains("Telemetry", StringComparison.OrdinalIgnoreCase), path);
                Assert.IsFalse(text.Contains("HttpClient", StringComparison.Ordinal), path);
                Assert.IsFalse(text.Contains("Environment.SpecialFolder", StringComparison.Ordinal), path);
            }
    }
}
