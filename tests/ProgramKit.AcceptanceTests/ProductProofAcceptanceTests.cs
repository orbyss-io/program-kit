using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ProductProofAcceptanceTests
{
    [TestMethod]
    public void Explain_is_sub_two_seconds_and_invariant_to_supported_culture_and_selection_order()
    {
        string firstWorkspace = TestRepository.CreateWorkspace();
        string secondWorkspace = TestRepository.CreateWorkspace();
        try
        {
            string secondRequestPath = Path.Combine(secondWorkspace, "requests", "explain.json");
            JsonObject reordered = CanonicalJson.Parse(File.ReadAllBytes(secondRequestPath)).AsObject();
            JsonArray selections = reordered["selections"]!.AsArray();
            reordered["selections"] = new JsonArray(selections.Reverse().Select(static item => item!.DeepClone()).ToArray());
            File.WriteAllBytes(secondRequestPath, CanonicalJson.Encode(reordered));

            Stopwatch timer = Stopwatch.StartNew();
            var first = TestRepository.RunCliWithEnvironment(
                Culture("en_US.UTF-8"),
                "explain", "--workspace", firstWorkspace,
                "--request", Path.Combine(firstWorkspace, "requests", "explain.json"), "--format", "json");
            timer.Stop();
            var second = TestRepository.RunCliWithEnvironment(
                Culture("nl_NL.UTF-8"),
                "explain", "--workspace", secondWorkspace,
                "--request", secondRequestPath, "--format", "json");
            Assert.AreEqual(0, first.ExitCode, first.StandardOutput + first.StandardError);
            Assert.AreEqual(0, second.ExitCode, second.StandardOutput + second.StandardError);
            Assert.IsTrue(timer.Elapsed < TimeSpan.FromSeconds(2), $"Explain took {timer.Elapsed}.");
            JsonObject firstResult = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, first.StandardOutput);
            JsonObject secondResult = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, second.StandardOutput);
            Assert.AreEqual(firstResult["requestIdentity"]!.GetValue<string>(), secondResult["requestIdentity"]!.GetValue<string>());
            Assert.AreEqual(firstResult["constructionIdentity"]!.GetValue<string>(), secondResult["constructionIdentity"]!.GetValue<string>());
            CollectionAssert.AreEqual(CanonicalJson.Encode(firstResult["explanation"]!), CanonicalJson.Encode(secondResult["explanation"]!));
        }
        finally
        {
            TestRepository.DeleteWorkspace(firstWorkspace);
            TestRepository.DeleteWorkspace(secondWorkspace);
        }
    }

    [TestMethod]
    public void Equal_construction_identities_have_equal_canonical_bytes_and_exact_package_claims()
    {
        string firstWorkspace = TestRepository.CreateWorkspace(includeMirror: true);
        string secondWorkspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            JsonObject firstResult = Construct(firstWorkspace, "en_US.UTF-8");
            JsonObject secondResult = Construct(secondWorkspace, "nl_NL.UTF-8");
            Assert.AreEqual(firstResult["constructionIdentity"]!.GetValue<string>(), secondResult["constructionIdentity"]!.GetValue<string>());

            JsonObject firstReceipt = ContractAssertions.ReadAndValidate(ContractAssertions.ConstructionReceipt, Path.Combine(firstWorkspace, ".program-kit", "construction-receipt.json"));
            JsonObject secondReceipt = ContractAssertions.ReadAndValidate(ContractAssertions.ConstructionReceipt, Path.Combine(secondWorkspace, ".program-kit", "construction-receipt.json"));
            Dictionary<string, string> firstCanonical = CanonicalClaims(firstReceipt);
            Dictionary<string, string> secondCanonical = CanonicalClaims(secondReceipt);
            CollectionAssert.AreEqual(firstCanonical.Keys.OrderBy(static item => item, StringComparer.Ordinal).ToArray(), secondCanonical.Keys.OrderBy(static item => item, StringComparer.Ordinal).ToArray());
            string[] differences = firstCanonical.Keys
                .Where(logicalPath => !string.Equals(firstCanonical[logicalPath], secondCanonical[logicalPath], StringComparison.Ordinal))
                .OrderBy(static logicalPath => logicalPath, StringComparer.Ordinal)
                .Select(logicalPath => $"{logicalPath}: {firstCanonical[logicalPath]} != {secondCanonical[logicalPath]}").ToArray();
            Assert.AreEqual(0, differences.Length, string.Join(Environment.NewLine, differences));

            JsonObject package = firstReceipt["artifacts"]!.AsArray().Select(static item => item!.AsObject())
                .Single(static item => item["claimClass"]!.GetValue<string>() == "verified-equivalent"
                    && item["artifact"]!["logicalPath"]!.GetValue<string>() == "feeds/component/Reference.Status.1.0.0.nupkg");
            string packageDigest = package["artifact"]!["digest"]!.GetValue<string>();
            JsonObject binding = CanonicalJson.Parse(File.ReadAllBytes(Path.Combine(firstWorkspace, "products", "Reference.Status.Api", "program-kit.package-binding.json"))).AsObject();
            Assert.AreEqual(packageDigest, binding["digest"]!.GetValue<string>());
            Assert.AreEqual(firstResult["constructionIdentity"]!.GetValue<string>(), binding["producerConstructionIdentity"]!.GetValue<string>());
            string project = File.ReadAllText(Path.Combine(firstWorkspace, "products", "Reference.Status.Api", "Reference.Status.Api.csproj"));
            StringAssert.Contains(project, "PackageReference Include=\"Reference.Status\" Version=\"[1.0.0]\"");
            Assert.IsTrue(firstReceipt["gateResults"]!.AsArray().All(static item => item!["status"]!.GetValue<string>() == "passed"));
        }
        finally
        {
            TestRepository.DeleteWorkspace(firstWorkspace);
            TestRepository.DeleteWorkspace(secondWorkspace);
        }
    }

    [TestMethod]
    public void Reparse_point_request_is_rejected_before_intake_and_without_effect()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            string link = Path.Combine(workspace, "requests", "linked.json");
            File.CreateSymbolicLink(link, Path.Combine(workspace, "requests", "explain.json"));
            string before = TestRepository.DigestTree(workspace);
            var execution = TestRepository.RunCli("explain", "--workspace", workspace, "--request", link, "--format", "json");
            Assert.AreEqual(3, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            Assert.AreEqual("request", result["furthestPhase"]!.GetValue<string>());
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static JsonObject Construct(string workspace, string culture)
    {
        var execution = TestRepository.RunCliWithEnvironment(
            Culture(culture),
            "construct", "--workspace", workspace,
            "--request", Path.Combine(workspace, "requests", "construct.json"), "--format", "json");
        Assert.AreEqual(0, execution.ExitCode, execution.StandardOutput + execution.StandardError);
        return ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
    }

    private static Dictionary<string, string> CanonicalClaims(JsonObject receipt) => receipt["artifacts"]!.AsArray()
        .Select(static item => item!.AsObject())
        .Where(static item => item["claimClass"]!.GetValue<string>() == "canonical-byte")
        .ToDictionary(
            static item => item["artifact"]!["logicalPath"]!.GetValue<string>(),
            static item => item["artifact"]!["digest"]!.GetValue<string>(),
            StringComparer.Ordinal);

    private static IReadOnlyDictionary<string, string> Culture(string value) => new Dictionary<string, string>(StringComparer.Ordinal)
    {
        ["LANG"] = value,
        ["LC_ALL"] = value,
        ["DOTNET_CLI_UI_LANGUAGE"] = value.StartsWith("nl", StringComparison.Ordinal) ? "nl-NL" : "en-US",
    };
}
