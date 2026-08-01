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
public sealed class ClaudeRuntimeIsolationAcceptanceTests
{
    [TestMethod]
    public void Reference_runtime_projects_have_no_session_or_provider_project_reference()
    {
        string templates = string.Join('\n', Directory.EnumerateFiles(Path.Combine(TestRepository.Root, "src", "ProgramKit.Providers.DotNet"), "*.cs", SearchOption.AllDirectories).Select(File.ReadAllText));
        Assert.IsGreaterThan(0, templates.Length);
        Assert.IsFalse(templates.Contains("ProgramKit.SessionIntegration", StringComparison.Ordinal));
        Assert.IsFalse(templates.Contains("ProgramKit.SessionIntegration.Providers.ClaudeCode", StringComparison.Ordinal));
        Assert.IsFalse(templates.Contains(".claude/skills", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(templates.Contains("Claude Code", StringComparison.OrdinalIgnoreCase));
    }

    [TestMethod]
    public void Generated_application_restores_builds_tests_and_runs_from_runtime_only_boundary()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        string isolated = TestRepository.CreateEmptyWorkspace();
        try
        {
            var construct = TestRepository.RunCli("construct", "--workspace", workspace, "--request", Path.Combine(workspace, "requests", "construct.yaml"), "--format", "json");
            Assert.AreEqual(0, construct.ExitCode, construct.StandardOutput + construct.StandardError);

            CopyTree(Path.Combine(workspace, "products", "Reference.Status.Api"), Path.Combine(isolated, "products", "Reference.Status.Api"));
            CopyTree(Path.Combine(workspace, "feeds"), Path.Combine(isolated, "feeds"));
            string app = Path.Combine(isolated, "products", "Reference.Status.Api");
            string config = Path.Combine(app, "NuGet.Config");
            File.WriteAllText(config, File.ReadAllText(config).Replace(workspace, isolated, StringComparison.OrdinalIgnoreCase));
            TestRepository.DeleteWorkspace(workspace);

            Assert.IsFalse(Directory.EnumerateFileSystemEntries(isolated, "*", SearchOption.AllDirectories)
                .Select(path => Path.GetRelativePath(isolated, path).Replace(Path.DirectorySeparatorChar, '/'))
                .Any(static path => path.StartsWith(".program-kit", StringComparison.OrdinalIgnoreCase) ||
                                    path.StartsWith(".specify", StringComparison.OrdinalIgnoreCase) ||
                                    path.StartsWith(".agents", StringComparison.OrdinalIgnoreCase) ||
                                    path.StartsWith(".claude", StringComparison.OrdinalIgnoreCase)));

            ProcessResult restore = Run("dotnet", app, "restore", "Reference.Status.Api.csproj", "--locked-mode", "--configfile", "NuGet.Config", "--packages", Path.Combine(isolated, ".runtime-packages"), "--no-cache");
            Assert.AreEqual(0, restore.ExitCode, restore.Output);
            ProcessResult build = Run("dotnet", app, "build", "Reference.Status.Api.csproj", "--configuration", "Release", "--no-restore");
            Assert.AreEqual(0, build.ExitCode, build.Output);
            ProcessResult test = Run("dotnet", app, "test", "Reference.Status.Api.csproj", "--configuration", "Release", "--no-build", "--no-restore");
            Assert.AreEqual(0, test.ExitCode, test.Output);

            string dependencies = File.ReadAllText(Path.Combine(app, "bin", "Release", "net10.0", "Reference.Status.Api.deps.json"));
            foreach (string forbidden in new[] { "ProgramKit", "SpecKit", "SessionIntegration", "Codex", "Claude" })
                Assert.IsFalse(dependencies.Contains(forbidden, StringComparison.OrdinalIgnoreCase), forbidden);

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
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
            TestRepository.DeleteWorkspace(isolated);
        }
    }

    private static void CopyTree(string source, string destination)
    {
        foreach (string directory in Directory.EnumerateDirectories(source, "*", SearchOption.AllDirectories))
            Directory.CreateDirectory(Path.Combine(destination, Path.GetRelativePath(source, directory)));
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source, "*", SearchOption.AllDirectories))
        {
            string target = Path.Combine(destination, Path.GetRelativePath(source, file));
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(file, target);
        }
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
        string appData = Path.Combine(workingDirectory, ".runtime-appdata");
        Directory.CreateDirectory(Path.Combine(appData, "NuGet"));
        start.Environment["APPDATA"] = appData;
        start.Environment["XDG_CONFIG_HOME"] = appData;
        start.Environment["DOTNET_CLI_HOME"] = Path.Combine(workingDirectory, ".runtime-dotnet-home");
        start.Environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1";
        start.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
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
