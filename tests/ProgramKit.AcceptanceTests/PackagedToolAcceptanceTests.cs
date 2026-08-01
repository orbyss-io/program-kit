using System;
using System.IO;
using System.Linq;
using System.Security;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class PackagedToolAcceptanceTests
{
    [TestMethod]
    public void Package_contract_is_workspace_local_and_has_no_runtime_or_global_registration_path()
    {
        string project = File.ReadAllText(Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "ProgramKit.Cli.csproj"));
        StringAssert.Contains(project, "<PackAsTool>true</PackAsTool>");
        StringAssert.Contains(project, "<ToolCommandName>program-kit</ToolCommandName>");
        Assert.IsFalse(project.Contains("DotnetToolSettings.xml", StringComparison.OrdinalIgnoreCase));

        string source = string.Join('\n', Directory.EnumerateFiles(Path.Combine(TestRepository.Root, "src", "ProgramKit.SessionIntegration"), "*.cs", SearchOption.AllDirectories).Select(File.ReadAllText));
        Assert.IsFalse(source.Contains("Environment.SpecialFolder", StringComparison.Ordinal));
        Assert.IsFalse(source.Contains("HttpClient", StringComparison.Ordinal));
    }

    [TestMethod]
    public void Exact_package_installs_and_runs_from_an_isolated_offline_workspace()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        string packageProject = Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "ProgramKit.Cli.csproj");
        (int packExit, _, string packError) = Run("dotnet", TestRepository.Root, "pack", packageProject, "-c", "Release", "--no-build", "--no-restore", "--output", workspace.Feed);
        Assert.AreEqual(0, packExit, packError);

        string config = Path.Combine(workspace.Root, "NuGet.Config");
        string feed = SecurityElement.Escape(workspace.Feed) ?? throw new InvalidOperationException("Local feed path could not be encoded.");
        File.WriteAllText(config, $"<?xml version=\"1.0\" encoding=\"utf-8\"?><configuration><packageSources><clear/><add key=\"local\" value=\"{feed}\"/></packageSources></configuration>");
        string toolPath = Path.Combine(workspace.Root, ".program-kit", "tools");
        (int installExit, _, string installError) = Run("dotnet", workspace.Root, "tool", "install", "Orbyss.ProgramKit.Cli", "--tool-path", toolPath, "--version", "1.0.0-alpha.1", "--configfile", config, "--no-cache");
        Assert.AreEqual(0, installExit, installError);

        string executable = Path.Combine(toolPath, OperatingSystem.IsWindows() ? "program-kit.exe" : "program-kit");
        (int versionExit, string versionOutput, string versionError) = Run(executable, workspace.Root, "version", "--format", "json");
        Assert.AreEqual(0, versionExit, versionError);
        JsonNode result = JsonNode.Parse(versionOutput) ?? throw new InvalidDataException("The packaged tool did not return JSON.");
        Assert.AreEqual("1.0.0-alpha.1", result["utility"]!["cli"]!.GetValue<string>());
        Assert.AreEqual(0, Directory.EnumerateFiles(workspace.Root, "*.csproj", SearchOption.AllDirectories).Count());
    }

    private static (int ExitCode, string Output, string Error) Run(string executable, string workingDirectory, params string[] arguments)
    {
        System.Diagnostics.ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        start.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        start.Environment["http_proxy"] = "http://127.0.0.1:1";
        start.Environment["https_proxy"] = "http://127.0.0.1:1";
        if (arguments.Length > 0 && string.Equals(arguments[0], "tool", StringComparison.Ordinal))
        {
            string appData = Path.Combine(workingDirectory, ".program-kit", "test-appdata");
            Directory.CreateDirectory(Path.Combine(appData, "NuGet"));
            start.Environment["APPDATA"] = appData;
            start.Environment["NUGET_PACKAGES"] = Path.Combine(workingDirectory, ".program-kit", "test-packages");
        }
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using System.Diagnostics.Process process = System.Diagnostics.Process.Start(start) ?? throw new InvalidOperationException("Could not start packaged-tool acceptance process.");
        string output = process.StandardOutput.ReadToEnd();
        string error = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return (process.ExitCode, output, error);
    }
}
