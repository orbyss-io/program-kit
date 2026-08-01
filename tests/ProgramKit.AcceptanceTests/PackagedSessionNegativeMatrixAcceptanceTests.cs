using System;
using System.Diagnostics;
using System.IO;
using System.Security;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class PackagedSessionNegativeMatrixAcceptanceTests
{
    [TestMethod]
    public void Packaged_cli_negative_matrix_is_typed_fail_closed_and_byte_preserving()
    {
        using SessionIntegrationTestWorkspace distribution = SessionIntegrationTestWorkspace.Create();
        string project = Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "ProgramKit.Cli.csproj");
        ProcessResult packed = Run("dotnet", TestRepository.Root, distribution.Root, "pack", project, "-c", "Release", "--no-restore", "--output", distribution.Feed);
        Assert.AreEqual(0, packed.ExitCode, packed.Error);

        using SessionIntegrationTestWorkspace requestFailures = InstallConsumer(distribution.Feed);
        requestFailures.Write("consumer-owned.txt", "preserved"u8.ToArray());
        string executable = Tool(requestFailures);
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(requestFailures.Root);

        string malformed = requestFailures.PathOf("requests/malformed.json");
        File.WriteAllText(malformed, "{}");
        AssertFailure(Invoke(executable, requestFailures.Root, "session", "explain", "--workspace", requestFailures.Root, "--request", malformed, "--format", "json"), "program-kit.kernel/PKREQ0002", "revise", "none");

        JsonObject missingExecutable = CanonicalJson.Parse(File.ReadAllBytes(requests.Explain)).AsObject();
        missingExecutable["cliRelease"]!["workspaceRelativeExecutable"] = ".program-kit/tools/unavailable.exe";
        string missingExecutablePath = requestFailures.PathOf("requests/unavailable-executable.json");
        File.WriteAllBytes(missingExecutablePath, CanonicalJson.Encode(missingExecutable));
        AssertFailure(Invoke(executable, requestFailures.Root, "session", "explain", "--workspace", requestFailures.Root, "--request", missingExecutablePath, "--format", "json"), "program-kit.session/PKSES0001", "stop", "none");

        JsonObject missingProvider = CanonicalJson.Parse(File.ReadAllBytes(requests.Explain)).AsObject();
        missingProvider["providerSelection"]!["provider"]!["selected"]!["name"] = "unavailable-provider";
        string missingProviderPath = requestFailures.PathOf("requests/missing-provider.json");
        File.WriteAllBytes(missingProviderPath, CanonicalJson.Encode(missingProvider));
        AssertFailure(Invoke(executable, requestFailures.Root, "session", "explain", "--workspace", requestFailures.Root, "--request", missingProviderPath, "--format", "json"), "program-kit.session/PKSES0002", "provide-input", "none");

        JsonObject stale = CanonicalJson.Parse(File.ReadAllBytes(requests.Install)).AsObject();
        stale["expectedInstallationState"] = "sha256:" + new string('7', 64);
        string stalePath = requestFailures.PathOf("requests/stale-install.json");
        File.WriteAllBytes(stalePath, CanonicalJson.Encode(stale));
        AssertFailure(Invoke(executable, requestFailures.Root, "session", "install", "--workspace", requestFailures.Root, "--request", stalePath, "--format", "json"), "program-kit.session/PKSES0004", "repair", "none");

        JsonObject missingAuthority = CanonicalJson.Parse(File.ReadAllBytes(requests.Install)).AsObject();
        missingAuthority.Remove("authorityGrant");
        string missingAuthorityPath = requestFailures.PathOf("requests/missing-authority.json");
        File.WriteAllBytes(missingAuthorityPath, CanonicalJson.Encode(missingAuthority));
        AssertFailure(Invoke(executable, requestFailures.Root, "session", "install", "--workspace", requestFailures.Root, "--request", missingAuthorityPath, "--format", "json"), "program-kit.kernel/PKPOL0001", "request-approval", "none");

        JsonObject ambiguous = CanonicalJson.Parse(File.ReadAllBytes(requests.Explain)).AsObject();
        ambiguous["providerSelection"]!["provider"]!["selected"]!["authority"] = "ambient";
        string ambiguousPath = requestFailures.PathOf("requests/ambiguous-session-provider.json");
        File.WriteAllBytes(ambiguousPath, CanonicalJson.Encode(ambiguous));
        AssertFailure(Invoke(executable, requestFailures.Root, "session", "explain", "--workspace", requestFailures.Root, "--request", ambiguousPath, "--format", "json"), "program-kit.kernel/PKRES0002", "provide-input", "none", 2);

        string unsupported = requestFailures.PathOf("requests/unsupported-factory.yaml");
        File.Copy(TestRepository.Fixture("Invalid/MissingSelection/requests/explain.yaml"), unsupported);
        AssertFailure(Invoke(executable, requestFailures.Root, "explain", "--workspace", requestFailures.Root, "--request", unsupported, "--format", "json"), "program-kit.kernel/PKRES0001", "provide-input", "none", 2);

        Assert.AreEqual("preserved", File.ReadAllText(requestFailures.PathOf("consumer-owned.txt")));
        Assert.IsFalse(File.Exists(requestFailures.PathOf(".agents/skills/program-kit/SKILL.md")));

        using SessionIntegrationTestWorkspace collision = InstallConsumer(distribution.Feed);
        collision.Write(".agents/skills/program-kit/SKILL.md", "consumer collision"u8.ToArray());
        SessionRequestPaths collisionRequests = SessionIntegrationFixture.WriteLifecycleRequests(collision.Root);
        AssertFailure(Invoke(Tool(collision), collision.Root, "session", "install", "--workspace", collision.Root, "--request", collisionRequests.Install, "--format", "json"), "program-kit.kernel/PKWSP0002", "repair", "none");
        Assert.AreEqual("consumer collision", File.ReadAllText(collision.PathOf(".agents/skills/program-kit/SKILL.md")));

        using SessionIntegrationTestWorkspace interrupted = InstallConsumer(distribution.Feed);
        SessionRequestPaths interruptedRequests = SessionIntegrationFixture.WriteLifecycleRequests(interrupted.Root);
        interrupted.Write(".program-kit/session-integrations/codex/staging/interrupted/marker", "prior attempt"u8.ToArray());
        AssertFailure(Invoke(Tool(interrupted), interrupted.Root, "session", "install", "--workspace", interrupted.Root, "--request", interruptedRequests.Install, "--format", "json"), "program-kit.kernel/PKWSP0003", "repair", "indeterminate");
        Assert.AreEqual("prior attempt", File.ReadAllText(interrupted.PathOf(".program-kit/session-integrations/codex/staging/interrupted/marker")));
        Assert.IsFalse(File.Exists(interrupted.PathOf(".agents/skills/program-kit/SKILL.md")));

        using SessionIntegrationTestWorkspace drift = InstallConsumer(distribution.Feed);
        SessionRequestPaths driftRequests = SessionIntegrationFixture.WriteLifecycleRequests(drift.Root);
        ProcessResult installed = Invoke(Tool(drift), drift.Root, "session", "install", "--workspace", drift.Root, "--request", driftRequests.Install, "--format", "json");
        Assert.AreEqual(0, installed.ExitCode, installed.Output);
        File.AppendAllText(drift.PathOf(".agents/skills/program-kit/SKILL.md"), "\nconsumer drift");
        string driftBytes = File.ReadAllText(drift.PathOf(".agents/skills/program-kit/SKILL.md"));
        AssertFailure(Invoke(Tool(drift), drift.Root, "session", "verify", "--workspace", drift.Root, "--request", driftRequests.Verify, "--format", "json"), "program-kit.session/PKSES0004", "repair", "none");
        Assert.AreEqual(driftBytes, File.ReadAllText(drift.PathOf(".agents/skills/program-kit/SKILL.md")));
    }

    private static SessionIntegrationTestWorkspace InstallConsumer(string feed)
    {
        SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        string config = workspace.PathOf("NuGet.Config");
        string encodedFeed = SecurityElement.Escape(Path.GetFullPath(feed)) ?? throw new InvalidOperationException("Feed path could not be encoded.");
        File.WriteAllText(config, $"<?xml version=\"1.0\" encoding=\"utf-8\"?><configuration><packageSources><clear/><add key=\"local\" value=\"{encodedFeed}\"/></packageSources></configuration>");
        ProcessResult installed = Run("dotnet", workspace.Root, workspace.Root, "tool", "install", "Orbyss.ProgramKit.Cli", "--tool-path", workspace.PathOf(".program-kit/tools"), "--version", "1.0.0-alpha.1", "--configfile", config, "--no-cache");
        if (installed.ExitCode != 0)
        {
            workspace.Dispose();
            Assert.Fail(installed.Error);
        }

        return workspace;
    }

    private static string Tool(SessionIntegrationTestWorkspace workspace) => workspace.PathOf(OperatingSystem.IsWindows() ? ".program-kit/tools/program-kit.exe" : ".program-kit/tools/program-kit");

    private static void AssertFailure(ProcessResult process, string diagnostic, string disposition, string effect, int expectedExitCode = 3)
    {
        JsonNode result = JsonNode.Parse(process.Output) ?? throw new InvalidDataException(process.Error);
        Assert.AreEqual(expectedExitCode, process.ExitCode, process.Output + process.Error);
        Assert.AreEqual(diagnostic, result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>(), process.Output);
        Assert.AreEqual(disposition, result["primaryDisposition"]!.GetValue<string>(), process.Output);
        Assert.AreEqual(effect, result["effectState"]!.GetValue<string>(), process.Output);
    }

    private static ProcessResult Invoke(string executable, string workspace, params string[] arguments) => Run(executable, workspace, workspace, arguments);

    private static ProcessResult Run(string executable, string workingDirectory, string environmentRoot, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        string appData = Path.Combine(environmentRoot, ".program-kit", "matrix-appdata");
        Directory.CreateDirectory(Path.Combine(appData, "NuGet"));
        start.Environment["APPDATA"] = appData;
        start.Environment["XDG_CONFIG_HOME"] = appData;
        start.Environment["DOTNET_CLI_HOME"] = Path.Combine(environmentRoot, ".program-kit", "matrix-home");
        start.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        start.Environment["MSBUILDDISABLENODEREUSE"] = "1";
        start.Environment["DOTNET_CLI_USE_MSBUILD_SERVER"] = "0";
        start.Environment["http_proxy"] = "http://127.0.0.1:1";
        start.Environment["https_proxy"] = "http://127.0.0.1:1";
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Could not start packaged negative-matrix process.");
        string output = process.StandardOutput.ReadToEnd();
        string error = process.StandardError.ReadToEnd();
        if (!process.WaitForExit(60_000))
        {
            process.Kill();
            throw new TimeoutException("Packaged negative-matrix process exceeded 60 seconds.");
        }

        return new ProcessResult(process.ExitCode, output, error);
    }

    private sealed record ProcessResult(int ExitCode, string Output, string Error);
}
