using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Providers.DotNet;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class NuGetIntegrityTests
{
    [TestMethod]
    public async Task Tampered_dependency_mirror_is_rejected_before_candidate_writes()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            string mirror = Path.Combine(workspace, "dependencies");
            string package = Directory.EnumerateFiles(mirror, "*.nupkg").OrderBy(static item => item, StringComparer.Ordinal).First();
            File.AppendAllBytes(package, new byte[] { 0 });
            string candidate = Path.Combine(workspace, ".candidate-test");
            JsonObject definition = JsonNode.Parse(File.ReadAllBytes(Path.Combine(workspace, "definitions", "reference-status.json")))!.AsObject();

            ProviderConstructionResult result = await new DotNetProvider().ConstructAsync(new ProviderConstructionContext(
                workspace,
                candidate,
                mirror,
                definition,
                $"sha256:{new string('2', 64)}",
                CancellationToken.None));

            Assert.IsFalse(result.Succeeded);
            CollectionAssert.Contains(result.Diagnostics.ToArray(), DiagnosticIds.ExternalUnavailable);
            Assert.IsFalse(Directory.Exists(candidate), "Mirror admission must fail before candidate writes.");
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public async Task Exact_dependency_mirror_is_admitted_and_constructs_provider_outputs()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            string mirror = Path.Combine(workspace, "dependencies");
            string candidate = Path.Combine(workspace, ".candidate-test");
            JsonObject definition = JsonNode.Parse(File.ReadAllBytes(Path.Combine(workspace, "definitions", "reference-status.json")))!.AsObject();
            ProviderConstructionResult result = await new DotNetProvider().ConstructAsync(new ProviderConstructionContext(
                workspace,
                candidate,
                mirror,
                definition,
                $"sha256:{new string('3', 64)}",
                CancellationToken.None));

            Assert.IsTrue(result.Succeeded, string.Join(Environment.NewLine, result.Diagnostics.Concat(result.Evidence.Select(static item => item.ToJsonString()))));
            JsonObject evidence = result.Evidence.Single();
            Assert.IsTrue(evidence["mirrorLockDigest"]!.GetValue<string>().StartsWith("sha256:", StringComparison.Ordinal));
            Assert.IsFalse(string.IsNullOrWhiteSpace(evidence["nugetContentHash"]!.GetValue<string>()));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }
}
