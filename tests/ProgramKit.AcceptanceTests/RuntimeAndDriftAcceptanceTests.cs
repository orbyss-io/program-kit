using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text.Json.Nodes;
using System.Threading;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class RuntimeAndDriftAcceptanceTests
{
    [TestMethod]
    public void GeneratedHostRunsWithoutProgramKitAndServesStatus()
    {
        string workspace = ConstructWorkspace();
        try
        {
            string app = Path.Combine(workspace, "products", "Reference.Status.Api");
            ProcessResult restore = Run("dotnet", app, "restore", "Reference.Status.Api.csproj", "--locked-mode", "--configfile", "NuGet.Config", "--packages", Path.Combine(workspace, ".runtime-packages"), "--no-cache");
            Assert.AreEqual(0, restore.ExitCode, restore.Output);
            ProcessResult build = Run("dotnet", app, "build", "Reference.Status.Api.csproj", "--configuration", "Release", "--no-restore");
            Assert.AreEqual(0, build.ExitCode, build.Output);
            string dependencies = File.ReadAllText(Path.Combine(app, "bin", "Release", "net10.0", "Reference.Status.Api.deps.json"));
            Assert.IsFalse(dependencies.Contains("ProgramKit", StringComparison.OrdinalIgnoreCase));

            int port = AvailablePort();
            ProcessStartInfo start = StartInfo("dotnet", app, Path.Combine(app, "bin", "Release", "net10.0", "Reference.Status.Api.dll"), "--urls", $"http://127.0.0.1:{port}");
            using Process process = Process.Start(start) ?? throw new InvalidOperationException("Unable to start generated host.");
            try
            {
                using HttpClient client = new();
                string? body = null;
                for (int attempt = 0; attempt < 50; attempt++)
                {
                    try { body = client.GetStringAsync($"http://127.0.0.1:{port}/status").GetAwaiter().GetResult(); break; }
                    catch (HttpRequestException) { Thread.Sleep(100); }
                }

                Assert.IsNotNull(body);
                Assert.AreEqual("operational", JsonNode.Parse(body)!["state"]!.GetValue<string>());
            }
            finally
            {
                if (!process.HasExited) process.Kill(entireProcessTree: true);
                process.WaitForExit();
            }
        }
        finally { TestRepository.DeleteWorkspace(workspace); }
    }

    [TestMethod]
    public void DriftIsDiagnosedWithoutMutation()
    {
        string workspace = ConstructWorkspace();
        try
        {
            File.AppendAllText(Path.Combine(workspace, "products", "Reference.Status.Api", "appsettings.json"), " ");
            string drifted = TestRepository.DigestTree(workspace);
            var evaluate = TestRepository.RunCli("evaluate", "--workspace", workspace, "--request", Path.Combine(workspace, "requests", "evaluate.json"), "--format", "json");
            Assert.AreNotEqual(0, evaluate.ExitCode);
            Assert.AreEqual(drifted, TestRepository.DigestTree(workspace));
            JsonNode result = JsonNode.Parse(evaluate.StandardOutput)!; string[] ids = result["diagnostics"]!["items"]!.AsArray().Select(item => item!["id"]!.GetValue<string>()).ToArray();
            ContractAssertions.AssertValid(ContractAssertions.OperationResult, result.AsObject());
            CollectionAssert.Contains(ids, "program-kit.kernel/PKWSP0001");
        }
        finally { TestRepository.DeleteWorkspace(workspace); }
    }

    private static string ConstructWorkspace()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        var construct = TestRepository.RunCli("construct", "--workspace", workspace, "--request", Path.Combine(workspace, "requests", "construct.json"), "--format", "json");
        if (construct.ExitCode != 0) { TestRepository.DeleteWorkspace(workspace); Assert.Fail(construct.StandardOutput + construct.StandardError); }
        return workspace;
    }

    private static ProcessResult Run(string executable, string workingDirectory, params string[] arguments)
    {
        using Process process = Process.Start(StartInfo(executable, workingDirectory, arguments)) ?? throw new InvalidOperationException("Unable to start child process.");
        string output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd();
        process.WaitForExit();
        return new ProcessResult(process.ExitCode, output);
    }

    private static ProcessStartInfo StartInfo(string executable, string workingDirectory, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        return start;
    }

    private static int AvailablePort()
    {
        TcpListener listener = new(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        return port;
    }

    private sealed record ProcessResult(int ExitCode, string Output);
}
