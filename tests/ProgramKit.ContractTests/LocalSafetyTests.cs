using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Xml.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed partial class LocalSafetyTests
{
    [TestMethod]
    public void Production_is_local_only_and_tool_processes_opt_out_of_telemetry()
    {
        string[] production = Directory.EnumerateFiles(Path.Combine(TestRepository.Root, "src"), "*.cs", SearchOption.AllDirectories)
            .Where(static path => !path.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase))
            .ToArray();
        string combined = string.Join('\n', production.Select(File.ReadAllText));
        Assert.IsFalse(combined.Contains("HttpClient", StringComparison.Ordinal));
        Assert.IsFalse(combined.Contains("System.Net.Sockets", StringComparison.Ordinal));
        Assert.IsFalse(combined.Contains("ApplicationInsights", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(combined.Contains("OpenTelemetry", StringComparison.OrdinalIgnoreCase));

        string runner = File.ReadAllText(Path.Combine(TestRepository.Root, "src", "ProgramKit.Providers.DotNet", "Construction", "DotNetToolRunner.cs"));
        StringAssert.Contains(runner, "DOTNET_CLI_TELEMETRY_OPTOUT");
        StringAssert.Contains(runner, "DOTNET_SKIP_FIRST_TIME_EXPERIENCE");
    }

    [TestMethod]
    public void Repository_graph_is_pinned_and_respects_architecture_boundaries()
    {
        foreach (string projectPath in Directory.EnumerateFiles(TestRepository.Root, "*.csproj", SearchOption.AllDirectories)
            .Where(static path => !path.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase)))
        {
            XDocument project = XDocument.Load(projectPath);
            Assert.IsTrue(project.Descendants("PackageReference").All(static package => package.Attribute("Version") is null), projectPath);
            Assert.IsTrue(File.Exists(Path.Combine(Path.GetDirectoryName(projectPath)!, "packages.lock.json")), projectPath);
        }

        AssertEdges("ProgramKit.Contracts", Array.Empty<string>());
        AssertEdges("ProgramKit.Kernel", new[] { "ProgramKit.Contracts" });
        AssertEdges("ProgramKit.Providers.DotNet", new[] { "ProgramKit.Contracts" });

        string templates = File.ReadAllText(Path.Combine(TestRepository.Root, "src", "ProgramKit.Providers.DotNet", "Templates", "DotNetTemplates.cs"));
        Assert.IsFalse(ForbiddenRuntimeReference().IsMatch(templates));
    }

    [TestMethod]
    public void Source_fixtures_and_evidence_do_not_contain_secret_assignments_or_self_host_bootstrap()
    {
        string[] roots = { "src", "tests/Fixtures", "artifacts/evidence", "eng" };
        foreach (string relativeRoot in roots)
        {
            string absoluteRoot = Path.Combine(TestRepository.Root, relativeRoot.Replace('/', Path.DirectorySeparatorChar));
            foreach (string path in Directory.EnumerateFiles(absoluteRoot, "*", SearchOption.AllDirectories)
                .Where(static path => !path.Contains($"{Path.DirectorySeparatorChar}bin{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase)
                    && !path.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase)
                    && !path.EndsWith(".nupkg", StringComparison.OrdinalIgnoreCase)))
            {
                string text = File.ReadAllText(path);
                Assert.IsFalse(SecretAssignment().IsMatch(text), path);
            }
        }

        string quickstart = File.ReadAllText(Path.Combine(TestRepository.Root, "eng", "Invoke-VerticalSliceQuickstart.ps1"));
        Assert.IsFalse(Regex.IsMatch(quickstart, @"(?im)^\s*(?:&\s*)?(?:\.\\)?program-kit(?:\.exe)?\s", RegexOptions.CultureInvariant));
    }

    private static void AssertEdges(string projectName, IReadOnlyCollection<string> allowed)
    {
        string projectPath = Path.Combine(TestRepository.Root, "src", projectName, $"{projectName}.csproj");
        XDocument project = XDocument.Load(projectPath);
        string[] references = project.Descendants("ProjectReference")
            .Select(reference => Path.GetFileNameWithoutExtension(reference.Attribute("Include")!.Value.Replace('\\', '/')))
            .ToArray();
        CollectionAssert.AreEquivalent(allowed.ToArray(), references, projectPath);
    }

    [GeneratedRegex("(?i)(?:api[_-]?key|client[_-]?secret|password|access[_-]?token)\\s*[:=]\\s*[\\\"'](?!\\$\\(|\\{\\{|<|example|placeholder)[^\\\"']{8,}[\\\"']", RegexOptions.CultureInvariant)]
    private static partial Regex SecretAssignment();

    [GeneratedRegex(@"(?i)(?:PackageReference|ProjectReference)[^\r\n]*(?:ProgramKit|SpecKit|OpenAI)", RegexOptions.CultureInvariant)]
    private static partial Regex ForbiddenRuntimeReference();
}
