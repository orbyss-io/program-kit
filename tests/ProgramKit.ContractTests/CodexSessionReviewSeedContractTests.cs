using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class CodexSessionReviewSeedContractTests
{
    [TestMethod]
    public void Exact_review_seed_passes_the_real_read_only_preflight()
    {
        using SeedWorkspace seed = SeedWorkspace.Create();

        ProcessResult result = Preflight(seed.Root);

        Assert.AreEqual(0, result.ExitCode, result.Error);
        JsonObject document = JsonNode.Parse(result.Output)?.AsObject() ?? throw new AssertFailedException("Expected preflight JSON.");
        Assert.AreEqual("ready", document["status"]!.GetValue<string>());
        Assert.AreEqual(9, document["staticFileCount"]!.GetValue<int>());
        Assert.AreEqual("dependencies", document["dependencyMirror"]!["logicalPath"]!.GetValue<string>());
        Assert.IsTrue(document["dependencyMirror"]!["lockDigest"]!.GetValue<string>().StartsWith("sha256:", StringComparison.Ordinal));
        Assert.IsTrue(document["dependencyMirror"]!["fileCount"]!.GetValue<int>() > 1);
        Assert.AreEqual("authority/construct-grant.json", document["constructAuthorityGrant"]!["logicalPath"]!.GetValue<string>());
        Assert.IsTrue(document["constructAuthorityGrant"]!["digest"]!.GetValue<string>().StartsWith("sha256:", StringComparison.Ordinal));
    }

    [TestMethod]
    public void Review_seed_preflight_rejects_missing_stale_and_zero_digest_inputs()
    {
        using SeedWorkspace missingReview = SeedWorkspace.Create();
        File.Delete(missingReview.PathOf("authority/review.json"));
        AssertFailed(missingReview.Root, "missing 'authority/review.json'");

        using SeedWorkspace missingRevocation = SeedWorkspace.Create();
        File.Delete(missingRevocation.PathOf("authority/revocations.json"));
        AssertFailed(missingRevocation.Root, "missing 'authority/revocations.json'");

        using SeedWorkspace staleBinding = SeedWorkspace.Create();
        File.AppendAllText(staleBinding.PathOf("requests/construct.json"), " ");
        AssertFailed(staleBinding.Root, "stale or mismatched bytes");

        using SeedWorkspace zeroDigest = SeedWorkspace.Create();
        string grant = File.ReadAllText(zeroDigest.PathOf("authority/construct-grant.json"));
        string firstDigest = "sha256:" + new string(grant[(grant.IndexOf("sha256:", StringComparison.Ordinal) + 7)..].Take(64).ToArray());
        File.WriteAllText(zeroDigest.PathOf("authority/construct-grant.json"), grant.Replace(firstDigest, "sha256:" + new string('0', 64), StringComparison.Ordinal));
        AssertFailed(zeroDigest.Root, "zero digest");

        using SeedWorkspace missingMirror = SeedWorkspace.Create();
        Directory.Delete(missingMirror.PathOf("dependencies"), recursive: true);
        AssertFailed(missingMirror.Root, "dependency mirror is missing");

        using SeedWorkspace changedMirror = SeedWorkspace.Create();
        File.AppendAllText(Directory.EnumerateFiles(changedMirror.PathOf("dependencies"), "*.nupkg").First(), "changed");
        AssertFailed(changedMirror.Root, "dependency mirror artifact is missing or changed");

        using SeedWorkspace extraMirror = SeedWorkspace.Create();
        File.WriteAllText(Path.Combine(extraMirror.PathOf("dependencies"), "extra.nupkg"), "extra");
        AssertFailed(extraMirror.Root, "case-colliding artifacts");

        using SeedWorkspace directoryMirror = SeedWorkspace.Create();
        Directory.CreateDirectory(Path.Combine(directoryMirror.PathOf("dependencies"), "extra"));
        AssertFailed(directoryMirror.Root, "undeclared directories");
    }

    private static void AssertFailed(string seed, string expected)
    {
        ProcessResult result = Preflight(seed);
        Assert.AreNotEqual(0, result.ExitCode);
        string diagnostic = Regex.Replace(
            result.Output + result.Error,
            "\\u001B\\[[0-?]*[ -/]*[@-~]",
            string.Empty,
            RegexOptions.CultureInvariant);
        diagnostic = Regex.Replace(diagnostic, "\\s+", " ", RegexOptions.CultureInvariant);
        StringAssert.Contains(diagnostic, expected);
    }

    private static ProcessResult Preflight(string seed)
    {
        ProcessStartInfo start = new("pwsh")
        {
            WorkingDirectory = TestRepository.Root,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        start.ArgumentList.Add("-NoProfile");
        start.ArgumentList.Add("-File");
        start.ArgumentList.Add(Path.Combine(TestRepository.Root, "eng", "Assert-CodexSessionReviewSeed.ps1"));
        start.ArgumentList.Add("-SeedRoot");
        start.ArgumentList.Add(seed);
        start.ArgumentList.Add("-StaticOnly");
        using Process process = Process.Start(start) ?? throw new AssertFailedException("Could not start the review-seed preflight.");
        string output = process.StandardOutput.ReadToEnd();
        string error = process.StandardError.ReadToEnd();
        Assert.IsTrue(process.WaitForExit(20_000), "Review-seed preflight timed out.");
        return new ProcessResult(process.ExitCode, output.Trim(), error.Trim());
    }

    private sealed class SeedWorkspace : IDisposable
    {
        private SeedWorkspace(string root) => Root = root;

        public string Root { get; }

        public static SeedWorkspace Create()
        {
            string root = Path.Combine(Path.GetTempPath(), "program-kit-codex-seed-contract-" + Guid.NewGuid().ToString("N"));
            string source = TestRepository.Fixture("Valid");
            JsonObject contract = JsonNode.Parse(File.ReadAllText(Path.Combine(TestRepository.Root, "specs", "002-session-integration-proof", "contracts", "codex-session-review-seed.json")))!.AsObject();
            foreach (JsonNode? item in contract["files"]!.AsArray())
            {
                string logicalPath = item!["logicalPath"]!.GetValue<string>();
                string target = Path.Combine(root, logicalPath.Replace('/', Path.DirectorySeparatorChar));
                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                File.Copy(Path.Combine(source, logicalPath.Replace('/', Path.DirectorySeparatorChar)), target);
            }
            CopyDirectory(
                Path.Combine(TestRepository.Root, "artifacts", "dependency-mirror"),
                Path.Combine(root, contract["dependencyMirror"]!["logicalPath"]!.GetValue<string>()));
            return new SeedWorkspace(root);
        }

        public string PathOf(string logicalPath) => Path.Combine(Root, logicalPath.Replace('/', Path.DirectorySeparatorChar));

        public void Dispose()
        {
            string temporaryRoot = Path.GetFullPath(Path.GetTempPath()).TrimEnd(Path.DirectorySeparatorChar);
            string resolved = Path.GetFullPath(Root);
            if (resolved.StartsWith(temporaryRoot + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) && Directory.Exists(resolved))
                Directory.Delete(resolved, recursive: true);
        }

        private static void CopyDirectory(string source, string destination)
        {
            Directory.CreateDirectory(destination);
            foreach (string file in Directory.EnumerateFiles(source))
                File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        }
    }

    private sealed record ProcessResult(int ExitCode, string Output, string Error);
}
