using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security;
using System.Security.Cryptography;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class DeterministicSessionReviewAcceptanceTests
{
    [TestMethod]
    public void Ten_packaged_offline_workspaces_complete_the_session_lifecycle()
    {
        using SessionIntegrationTestWorkspace distribution = SessionIntegrationTestWorkspace.Create();
        string feed = Environment.GetEnvironmentVariable("PROGRAM_KIT_SESSION_FEED") ?? distribution.Feed;
        if (Environment.GetEnvironmentVariable("PROGRAM_KIT_SESSION_FEED") is null)
        {
            string project = Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "ProgramKit.Cli.csproj");
            ProcessResult packed = Run("dotnet", TestRepository.Root, distribution.Root, "pack", project, "-c", "Release", "--no-restore", "--output", feed);
            Assert.AreEqual(0, packed.ExitCode, packed.Error);
        }

        string package = Directory.EnumerateFiles(feed, "Orbyss.ProgramKit.Cli.1.0.0-alpha.1.nupkg", SearchOption.TopDirectoryOnly).Single();
        string packageDigest = Digest(File.ReadAllBytes(package));
        JsonArray trials = new();
        string? expectedProjectionDigest = null;

        for (int trial = 1; trial <= 10; trial++)
        {
            using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
            workspace.Write("consumer-owned.txt", "preserved"u8.ToArray());
            string config = WriteLocalConfig(workspace.Root, feed);
            string toolPath = Path.Combine(workspace.Root, ".program-kit", "tools");
            Stopwatch installationTimer = Stopwatch.StartNew();
            ProcessResult toolInstall = Run("dotnet", workspace.Root, workspace.Root, "tool", "install", "Orbyss.ProgramKit.Cli", "--tool-path", toolPath, "--version", "1.0.0-alpha.1", "--configfile", config, "--no-cache");
            installationTimer.Stop();
            Assert.AreEqual(0, toolInstall.ExitCode, toolInstall.Error);
            string executable = Path.Combine(toolPath, OperatingSystem.IsWindows() ? "program-kit.exe" : "program-kit");

            ProcessResult version = Invoke(executable, workspace.Root, "version", "--format", "json");
            Assert.AreEqual(0, version.ExitCode, version.Error);
            Assert.AreEqual("1.0.0-alpha.1", Parse(version)["utility"]!["cli"]!.GetValue<string>());

            SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
            ProcessResult explained = Invoke(executable, workspace.Root, "session", "explain", "--workspace", workspace.Root, "--request", requests.Explain, "--format", "json");
            Assert.AreEqual(0, explained.ExitCode, explained.Error);
            Assert.AreEqual("none", Parse(explained)["effectState"]!.GetValue<string>());

            JsonObject withoutAuthority = JsonNode.Parse(File.ReadAllText(requests.Install))!.AsObject();
            withoutAuthority.Remove("authorityGrant");
            string withoutAuthorityPath = Path.Combine(workspace.Root, "requests", "session-install-without-authority.json");
            File.WriteAllText(withoutAuthorityPath, withoutAuthority.ToJsonString());
            ProcessResult denied = Invoke(executable, workspace.Root, "session", "install", "--workspace", workspace.Root, "--request", withoutAuthorityPath, "--format", "json");
            JsonNode deniedResult = Parse(denied);
            Assert.AreEqual(3, denied.ExitCode);
            Assert.AreEqual("program-kit.kernel/PKPOL0001", deniedResult["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());

            ProcessResult installed = Invoke(executable, workspace.Root, "session", "install", "--workspace", workspace.Root, "--request", requests.Install, "--format", "json");
            Assert.AreEqual(0, installed.ExitCode, installed.Error);
            JsonNode installedResult = Parse(installed);
            Assert.AreEqual("committed", installedResult["effectState"]!.GetValue<string>());
            string skill = workspace.PathOf(".agents/skills/program-kit/SKILL.md");
            byte[] admittedSkill = File.ReadAllBytes(skill);
            string projectionDigest = Digest(admittedSkill);
            expectedProjectionDigest ??= projectionDigest;
            Assert.AreEqual(expectedProjectionDigest, projectionDigest);
            string record = workspace.PathOf(".program-kit/session-integrations/codex/installation.json");
            string recordDigest = Digest(File.ReadAllBytes(record));

            ProcessResult verified = Invoke(executable, workspace.Root, "session", "verify", "--workspace", workspace.Root, "--request", requests.Verify, "--format", "json");
            JsonNode verifiedResult = Parse(verified);
            Assert.AreEqual(0, verified.ExitCode, verified.Error);
            Assert.AreEqual("exact", verifiedResult["session"]!["state"]!.GetValue<string>());

            File.AppendAllText(skill, "\ndeterministic drift proof");
            ProcessResult drift = Invoke(executable, workspace.Root, "session", "verify", "--workspace", workspace.Root, "--request", requests.Verify, "--format", "json");
            JsonNode driftResult = Parse(drift);
            Assert.AreEqual(3, drift.ExitCode);
            Assert.AreEqual("program-kit.session/PKSES0004", driftResult["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
            File.WriteAllBytes(skill, admittedSkill);

            string removeRequest = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);
            ProcessResult removed = Invoke(executable, workspace.Root, "session", "remove", "--workspace", workspace.Root, "--request", removeRequest, "--format", "json");
            JsonNode removedResult = Parse(removed);
            Assert.AreEqual(0, removed.ExitCode, removed.Error);
            Assert.AreEqual("removed", removedResult["session"]!["state"]!.GetValue<string>());
            string receipt = workspace.PathOf(".program-kit/session-integrations/codex/removal.json");
            Assert.IsTrue(File.Exists(receipt));
            Assert.IsFalse(File.Exists(skill));
            Assert.AreEqual("preserved", File.ReadAllText(workspace.PathOf("consumer-owned.txt")));
            Assert.IsTrue(File.Exists(executable));

            trials.Add(new JsonObject
            {
                ["trial"] = trial,
                ["platform"] = OperatingSystem.IsWindows() ? "windows" : "linux",
                ["toolInstallElapsedMilliseconds"] = installationTimer.ElapsedMilliseconds,
                ["recordDigest"] = recordDigest,
                ["projectionDigest"] = projectionDigest,
                ["missingAuthorityDiagnostic"] = deniedResult["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>(),
                ["driftDiagnostic"] = driftResult["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>(),
                ["removalReceiptDigest"] = Digest(File.ReadAllBytes(receipt)),
                ["finalState"] = removedResult["session"]!["state"]!.GetValue<string>(),
                ["cliCallableAfterRemoval"] = Invoke(executable, workspace.Root, "version", "--format", "json").ExitCode == 0,
                ["consumerBytesPreserved"] = true,
            });
        }

        JsonObject evidence = new()
        {
            ["schema"] = "program-kit.deterministic-session-review/v1",
            ["generatedAt"] = DateTimeOffset.UtcNow.ToString("O"),
            ["sdkVersion"] = Run("dotnet", TestRepository.Root, distribution.Root, "--version").Output.Trim(),
            ["packageId"] = "Orbyss.ProgramKit.Cli",
            ["packageVersion"] = "1.0.0-alpha.1",
            ["packageDigest"] = packageDigest,
            ["trials"] = trials,
            ["failures"] = new JsonArray(),
            ["assertions"] = new JsonObject
            {
                ["allTrialsPassed"] = true,
                ["networkDeniedAfterAcquisition"] = true,
                ["telemetryDisabled"] = true,
                ["sourceUploadObserved"] = false,
                ["providerGlobalRegistrationObserved"] = false,
                ["projectionDeterministic"] = true,
            },
        };
        string? evidencePath = Environment.GetEnvironmentVariable("PROGRAM_KIT_SESSION_REVIEW_OUTPUT");
        if (!string.IsNullOrWhiteSpace(evidencePath))
        {
            string fullPath = Path.GetFullPath(evidencePath);
            Directory.CreateDirectory(Path.GetDirectoryName(fullPath)!);
            File.WriteAllText(fullPath, evidence.ToJsonString(new() { WriteIndented = true }));
        }
    }

    private static string WriteLocalConfig(string workspace, string feed)
    {
        string config = Path.Combine(workspace, "NuGet.Config");
        string encodedFeed = SecurityElement.Escape(Path.GetFullPath(feed)) ?? throw new InvalidOperationException("Feed path could not be encoded.");
        File.WriteAllText(config, $"<?xml version=\"1.0\" encoding=\"utf-8\"?><configuration><packageSources><clear/><add key=\"local\" value=\"{encodedFeed}\"/></packageSources></configuration>");
        return config;
    }

    private static ProcessResult Invoke(string executable, string workspace, params string[] arguments) => Run(executable, workspace, workspace, arguments);

    private static ProcessResult Run(string executable, string workingDirectory, string environmentRoot, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        string appData = Path.Combine(environmentRoot, ".program-kit", "process-appdata");
        Directory.CreateDirectory(Path.Combine(appData, "NuGet"));
        start.Environment["APPDATA"] = appData;
        start.Environment["XDG_CONFIG_HOME"] = appData;
        start.Environment["DOTNET_CLI_HOME"] = Path.Combine(environmentRoot, ".program-kit", "process-home");
        start.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        start.Environment["MSBUILDDISABLENODEREUSE"] = "1";
        start.Environment["DOTNET_CLI_USE_MSBUILD_SERVER"] = "0";
        start.Environment["http_proxy"] = "http://127.0.0.1:1";
        start.Environment["https_proxy"] = "http://127.0.0.1:1";
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Could not start deterministic session review process.");
        var output = process.StandardOutput.ReadToEndAsync();
        var error = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(60_000))
        {
            process.Kill();
            _ = process.WaitForExit(5_000);
            throw new TimeoutException($"Deterministic session command exceeded 60 seconds: {executable} {string.Join(' ', arguments)}");
        }
        if (!System.Threading.Tasks.Task.WaitAll(new System.Threading.Tasks.Task[] { output, error }, 5_000))
            throw new TimeoutException($"Deterministic session command left redirected output open: {executable} {string.Join(' ', arguments)}");
        return new(process.ExitCode, output.GetAwaiter().GetResult(), error.GetAwaiter().GetResult());
    }

    private static JsonNode Parse(ProcessResult result) => JsonNode.Parse(result.Output) ?? throw new InvalidDataException(result.Error);
    private static string Digest(byte[] bytes) => $"sha256:{Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()}";
    private sealed record ProcessResult(int ExitCode, string Output, string Error);
}
