using System;
using System.Diagnostics;
using System.IO;
using System.Security;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class PackagedToolRemovalAcceptanceTests
{
    [TestMethod]
    public void Workspace_local_packaged_cli_remains_callable_after_projection_removal()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        string project = Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "ProgramKit.Cli.csproj");
        Assert.AreEqual(0, Run("dotnet", TestRepository.Root, workspace.Root, "pack", project, "-c", "Release", "--no-restore", "--output", workspace.Feed).ExitCode);
        string config = Path.Combine(workspace.Root, "NuGet.Config");
        string feed = SecurityElement.Escape(workspace.Feed) ?? throw new InvalidOperationException("Feed path could not be encoded.");
        File.WriteAllText(config, $"<?xml version=\"1.0\" encoding=\"utf-8\"?><configuration><packageSources><clear/><add key=\"local\" value=\"{feed}\"/></packageSources></configuration>");
        string toolPath = Path.Combine(workspace.Root, ".program-kit", "tools");
        ProcessResult installation = Run("dotnet", workspace.Root, workspace.Root, "tool", "install", "Orbyss.ProgramKit.Cli", "--tool-path", toolPath, "--version", "1.0.0-alpha.2", "--configfile", config, "--no-cache");
        Assert.AreEqual(0, installation.ExitCode, installation.Error);
        string executable = Path.Combine(toolPath, OperatingSystem.IsWindows() ? "program-kit.exe" : "program-kit");

        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        Assert.AreEqual(0, Run(executable, workspace.Root, workspace.Root, "session", "install", "--workspace", workspace.Root, "--request", requests.Install, "--format", "json").ExitCode);
        string remove = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);
        ProcessResult removed = Run(executable, workspace.Root, workspace.Root, "session", "remove", "--workspace", workspace.Root, "--request", remove, "--format", "json");
        Assert.AreEqual(0, removed.ExitCode, removed.Error + removed.Output);
        Assert.IsFalse(File.Exists(workspace.PathOf(".agents/skills/program-kit/SKILL.md")));
        ProcessResult version = Run(executable, workspace.Root, workspace.Root, "version", "--format", "json");
        Assert.AreEqual(0, version.ExitCode, version.Error);
        Assert.AreEqual("1.0.0-alpha.2", JsonNode.Parse(version.Output)!["utility"]!["cli"]!.GetValue<string>());
    }

    private static ProcessResult Run(string executable, string workingDirectory, string environmentRoot, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        string appData = Path.Combine(environmentRoot, ".packaged-removal-appdata");
        Directory.CreateDirectory(Path.Combine(appData, "NuGet"));
        start.Environment["APPDATA"] = appData;
        start.Environment["XDG_CONFIG_HOME"] = appData;
        start.Environment["DOTNET_CLI_HOME"] = Path.Combine(environmentRoot, ".packaged-removal-home");
        start.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        start.Environment["MSBUILDDISABLENODEREUSE"] = "1";
        start.Environment["DOTNET_CLI_USE_MSBUILD_SERVER"] = "0";
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Could not start packaged removal process.");
        var output = process.StandardOutput.ReadToEndAsync();
        var error = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(60_000))
        {
            process.Kill();
            _ = process.WaitForExit(5_000);
            throw new TimeoutException($"Packaged removal command exceeded 60 seconds: {executable} {string.Join(' ', arguments)}");
        }
        if (!System.Threading.Tasks.Task.WaitAll(new System.Threading.Tasks.Task[] { output, error }, 5_000))
            throw new TimeoutException($"Packaged removal command left redirected output open after exit: {executable} {string.Join(' ', arguments)}");
        return new(process.ExitCode, output.GetAwaiter().GetResult(), error.GetAwaiter().GetResult());
    }

    private sealed record ProcessResult(int ExitCode, string Output, string Error);
}
