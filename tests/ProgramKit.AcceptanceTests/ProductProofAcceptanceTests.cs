using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Xml.Linq;
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
    public void Equal_construction_identities_close_path_culture_input_order_and_external_package_claims()
    {
        string firstWorkspace = TestRepository.CreateWorkspace(includeMirror: true);
        string secondWorkspace = TestRepository.CreateWorkspace(includeMirror: true);
        string unicodeWorkspace = Path.Combine(
            Path.GetDirectoryName(secondWorkspace)!,
            $"variant-naive-路径-{Guid.NewGuid():N}");
        Directory.Move(secondWorkspace, unicodeWorkspace);
        secondWorkspace = unicodeWorkspace;
        try
        {
            string secondJsonRequest = Path.Combine(secondWorkspace, "requests", "construct.json");
            JsonObject request = CanonicalJson.Parse(File.ReadAllBytes(secondJsonRequest)).AsObject();
            JsonArray selections = request["selections"]!.AsArray();
            request["selections"] = new JsonArray(selections.Reverse().Select(static item => item!.DeepClone()).ToArray());
            JsonObject reversePropertyOrder = new();
            foreach ((string name, JsonNode? value) in request.Reverse())
            {
                reversePropertyOrder.Add(name, value?.DeepClone());
            }

            string yamlRequest = Path.Combine(secondWorkspace, "requests", "construct.yaml");
            File.WriteAllText(
                yamlRequest,
                reversePropertyOrder.ToJsonString(new JsonSerializerOptions { WriteIndented = true }),
                new UTF8Encoding(false));

            JsonObject firstResult = Construct(firstWorkspace, Path.Combine(firstWorkspace, "requests", "construct.json"), "en_US.UTF-8");
            JsonObject secondResult = Construct(secondWorkspace, yamlRequest, "tr_TR.UTF-8");
            Assert.AreEqual(firstResult["constructionIdentity"]!.GetValue<string>(), secondResult["constructionIdentity"]!.GetValue<string>());

            JsonObject firstReceipt = ContractAssertions.ReadAndValidate(ContractAssertions.ConstructionReceipt, Path.Combine(firstWorkspace, ".program-kit", "construction-receipt.json"));
            JsonObject secondReceipt = ContractAssertions.ReadAndValidate(ContractAssertions.ConstructionReceipt, Path.Combine(secondWorkspace, ".program-kit", "construction-receipt.json"));
            Dictionary<string, string> firstCanonical = CanonicalClaims(firstReceipt);
            Dictionary<string, string> secondCanonical = CanonicalClaims(secondReceipt);
            CollectionAssert.AreEqual(firstCanonical.Keys.OrderBy(static item => item, StringComparer.Ordinal).ToArray(), secondCanonical.Keys.OrderBy(static item => item, StringComparer.Ordinal).ToArray());
            foreach (string logicalPath in firstCanonical.Keys.OrderBy(static item => item, StringComparer.Ordinal))
            {
                Assert.AreEqual(firstCanonical[logicalPath], secondCanonical[logicalPath], logicalPath);
                CollectionAssert.AreEqual(
                    File.ReadAllBytes(Resolve(firstWorkspace, logicalPath)),
                    File.ReadAllBytes(Resolve(secondWorkspace, logicalPath)),
                    logicalPath);
            }

            VerifyExternalPackageClaim(firstWorkspace, firstReceipt, firstResult["constructionIdentity"]!.GetValue<string>());
            VerifyExternalPackageClaim(secondWorkspace, secondReceipt, secondResult["constructionIdentity"]!.GetValue<string>());
            Assert.IsTrue(firstReceipt["gateResults"]!.AsArray().All(static item => item!["status"]!.GetValue<string>() == "passed"));
            Assert.IsTrue(secondReceipt["gateResults"]!.AsArray().All(static item => item!["status"]!.GetValue<string>() == "passed"));
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

    private static JsonObject Construct(string workspace, string request, string culture)
    {
        var execution = TestRepository.RunCliWithEnvironment(
            Culture(culture),
            "construct", "--workspace", workspace,
            "--request", request, "--format", "json");
        Assert.AreEqual(0, execution.ExitCode, execution.StandardOutput + execution.StandardError);
        return ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
    }

    private static void VerifyExternalPackageClaim(string workspace, JsonObject receipt, string constructionIdentity)
    {
        const string logicalPath = "feeds/component/Reference.Status.1.0.0.nupkg";
        JsonObject package = receipt["artifacts"]!.AsArray().Select(static item => item!.AsObject())
            .Single(static item => item["artifact"]!["logicalPath"]!.GetValue<string>() == logicalPath);
        Assert.AreEqual("verified-equivalent", package["claimClass"]!.GetValue<string>());
        byte[] packageBytes = File.ReadAllBytes(Resolve(workspace, logicalPath));
        string sha256 = $"sha256:{Convert.ToHexString(SHA256.HashData(packageBytes)).ToLowerInvariant()}";
        string nugetContentHash = Convert.ToBase64String(SHA512.HashData(packageBytes));
        Assert.AreEqual(package["artifact"]!["digest"]!.GetValue<string>(), sha256);

        JsonObject binding = CanonicalJson.Parse(File.ReadAllBytes(Path.Combine(workspace, "products", "Reference.Status.Api", "program-kit.package-binding.json"))).AsObject();
        Assert.AreEqual("Reference.Status", binding["packageId"]!.GetValue<string>());
        Assert.AreEqual("1.0.0", binding["version"]!.GetValue<string>());
        Assert.AreEqual(sha256, binding["digest"]!.GetValue<string>());
        Assert.AreEqual(nugetContentHash, binding["nugetContentHash"]!.GetValue<string>());
        Assert.AreEqual(constructionIdentity, binding["producerConstructionIdentity"]!.GetValue<string>());

        using ZipArchive archive = new(new MemoryStream(packageBytes), ZipArchiveMode.Read, leaveOpen: false);
        ZipArchiveEntry specification = archive.Entries.Single(static entry => entry.FullName.EndsWith(".nuspec", StringComparison.OrdinalIgnoreCase));
        using Stream specificationStream = specification.Open();
        XDocument nuspec = XDocument.Load(specificationStream);
        Assert.AreEqual("Reference.Status", nuspec.Descendants().Single(static element => element.Name.LocalName == "id").Value);
        Assert.AreEqual("1.0.0", nuspec.Descendants().Single(static element => element.Name.LocalName == "version").Value);

        string project = File.ReadAllText(Path.Combine(workspace, "products", "Reference.Status.Api", "Reference.Status.Api.csproj"));
        StringAssert.Contains(project, "PackageReference Include=\"Reference.Status\" Version=\"[1.0.0]\"");
    }

    private static Dictionary<string, string> CanonicalClaims(JsonObject receipt) => receipt["artifacts"]!.AsArray()
        .Select(static item => item!.AsObject())
        .Where(static item => item["claimClass"]!.GetValue<string>() == "canonical-byte")
        .ToDictionary(
            static item => item["artifact"]!["logicalPath"]!.GetValue<string>(),
            static item => item["artifact"]!["digest"]!.GetValue<string>(),
            StringComparer.Ordinal);

    private static string Resolve(string workspace, string logicalPath) =>
        Path.GetFullPath(Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar)));

    private static IReadOnlyDictionary<string, string> Culture(string value) => new Dictionary<string, string>(StringComparer.Ordinal)
    {
        ["LANG"] = value,
        ["LC_ALL"] = value,
        ["DOTNET_CLI_UI_LANGUAGE"] = value.StartsWith("nl", StringComparison.Ordinal)
            ? "nl-NL"
            : value.StartsWith("tr", StringComparison.Ordinal) ? "tr-TR" : "en-US",
    };
}
