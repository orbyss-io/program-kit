using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Security;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class SpecKitAdapterPreparationAcceptanceTests
{
    [TestMethod]
    public void Staged_adapter_and_workspace_local_tool_prepare_reviewed_reference_status_without_product_effect()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace(restoreFactory: false);
        try
        {
            Dictionary<string, string> environment = IsolatedEnvironment(workspace);
            string feed = Path.Combine(workspace, ".program-kit", "feed");
            Directory.CreateDirectory(feed);
            string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent?.Name ?? throw new InvalidOperationException("Test configuration unavailable.");
            string project = Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "ProgramKit.Cli.csproj");
            AssertSucceeded(Run("dotnet", TestRepository.Root, environment, "pack", project, "--configuration", configuration, "--no-build", "--no-restore", "--output", feed));
            string nugetConfig = WriteNuGetConfig(workspace, feed);
            WriteToolManifest(workspace);
            AssertSucceeded(Run("dotnet", workspace, environment, "tool", "restore", "--configfile", nugetConfig, "--no-cache"));

            string restoreRequest = WorkspaceBootstrapFixture.WriteRequest(workspace, "restore-package.json", WorkspaceBootstrapFixture.RestoreRequest("factory"));
            AssertSucceeded(Run("dotnet", workspace, environment, "tool", "run", "program-kit", "--", "restore", "--workspace", workspace, "--request", restoreRequest, "--format", "json"));
            string adapterDll = StageAdapter(workspace, configuration);

            string validateRequest = WriteAdapterRequest(workspace, "validate");
            Stopwatch validationWatch = Stopwatch.StartNew();
            ProcessResult validation = Run("dotnet", workspace, environment, adapterDll, "validate", "--workspace", workspace, "--request", validateRequest, "--format", "json");
            validationWatch.Stop();
            AssertSucceeded(validation);
            Assert.IsTrue(validationWatch.Elapsed < TimeSpan.FromSeconds(2), validationWatch.Elapsed.ToString());
            AssertAdapterResult(validation.Output, "succeeded", "none");

            string prepareRequest = WriteAdapterRequest(workspace, "prepare");
            ProcessResult prepared = Run("dotnet", workspace, environment, adapterDll, "prepare", "--workspace", workspace, "--request", prepareRequest, "--format", "json");
            AssertSucceeded(prepared);
            JsonObject result = AssertAdapterResult(prepared.Output, "succeeded", "adapter-files-only");
            Assert.AreEqual("program-kit.operation-result/v2", result["programKitResult"]!["schema"]!.GetValue<string>());
            Assert.AreEqual("none", result["programKitResult"]!["effectState"]!.GetValue<string>());
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates")));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, "src", "Reference.Status")));
            string generatedRoot = Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "generated");
            Assert.IsTrue(File.Exists(Path.Combine(generatedRoot, "results", "prepare.json")));
            Assert.IsTrue(File.Exists(Path.Combine(generatedRoot, "results", "explain.json")));

            string beforeRepeat = TestRepository.DigestTree(workspace);
            ProcessResult repeated = Run("dotnet", workspace, environment, adapterDll, "prepare", "--workspace", workspace, "--request", prepareRequest, "--format", "json");
            AssertSucceeded(repeated);
            JsonObject repeatedResult = AssertAdapterResult(repeated.Output, "succeeded", "adapter-files-only");
            Assert.AreEqual(false, repeatedResult["payload"]!["changed"]!.GetValue<bool>());
            Assert.AreEqual(beforeRepeat, TestRepository.DigestTree(workspace));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static string StageAdapter(string workspace, string configuration)
    {
        string source = Path.Combine(TestRepository.Root, "src", "ProgramKit.SpecKitAdapter", "bin", configuration, "net10.0");
        string destination = Path.Combine(workspace, ".specify", "extensions", "orbyss-program-kit-adapter", "tools");
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source)) File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        string dll = Path.Combine(destination, "program-kit-spec-kit-adapter.dll");
        Assert.IsTrue(File.Exists(dll));
        return dll;
    }

    private static string WriteAdapterRequest(string workspace, string operation)
    {
        JsonObject request = SpecKitAdapterFixture.AdapterRequest(operation);
        string path = Path.Combine(workspace, "requests", $"adapter-{operation}.json");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllBytes(path, CanonicalDocument.Encode(request));
        return path;
    }

    private static string WriteNuGetConfig(string workspace, string feed)
    {
        string path = Path.Combine(workspace, "NuGet.Config");
        string escaped = SecurityElement.Escape(feed) ?? throw new InvalidOperationException("Feed path could not be encoded.");
        File.WriteAllText(path, $"<?xml version=\"1.0\" encoding=\"utf-8\"?><configuration><packageSources><clear/><add key=\"local\" value=\"{escaped}\"/></packageSources></configuration>");
        return path;
    }

    private static void WriteToolManifest(string workspace)
    {
        string path = Path.Combine(workspace, ".config", "dotnet-tools.json");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        JsonObject manifest = new()
        {
            ["version"] = 1,
            ["isRoot"] = true,
            ["tools"] = new JsonObject
            {
                ["orbyss.programkit.cli"] = new JsonObject
                {
                    ["version"] = "1.0.0-alpha.2",
                    ["commands"] = new JsonArray("program-kit"),
                    ["rollForward"] = false,
                },
            },
        };
        File.WriteAllBytes(path, CanonicalJson.Encode(manifest));
    }

    private static Dictionary<string, string> IsolatedEnvironment(string workspace)
    {
        string state = Path.Combine(workspace, ".program-kit", "dotnet-state");
        Directory.CreateDirectory(state);
        return new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["DOTNET_CLI_HOME"] = Path.Combine(state, "home"),
            ["NUGET_PACKAGES"] = Path.Combine(state, "packages"),
            ["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1",
            ["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1",
            ["DOTNET_NOLOGO"] = "1",
            ["NUGET_XMLDOC_MODE"] = "skip",
            ["http_proxy"] = "http://127.0.0.1:1",
            ["https_proxy"] = "http://127.0.0.1:1",
        };
    }

    private static JsonObject AssertAdapterResult(string output, string outcome, string effect)
    {
        JsonObject result = CanonicalDocument.Parse(System.Text.Encoding.UTF8.GetBytes(output)).AsObject();
        AdapterSchemaValidator.Validate("adapter-result.schema.json", result);
        Assert.AreEqual(outcome, result["outcome"]!.GetValue<string>());
        Assert.AreEqual(effect, result["effectState"]!.GetValue<string>());
        return result;
    }

    private static void AssertSucceeded(ProcessResult result) => Assert.AreEqual(0, result.ExitCode, result.Output + result.Error);

    private static ProcessResult Run(string executable, string workingDirectory, IReadOnlyDictionary<string, string> environment, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        foreach ((string key, string value) in environment) start.Environment[key] = value;
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException("Could not start acceptance process.");
        string output = process.StandardOutput.ReadToEnd();
        string error = process.StandardError.ReadToEnd();
        if (!process.WaitForExit(120_000))
        {
            process.Kill();
            throw new TimeoutException("Acceptance process exceeded two minutes.");
        }

        return new ProcessResult(process.ExitCode, output, error);
    }

    private sealed record ProcessResult(int ExitCode, string Output, string Error);
}
