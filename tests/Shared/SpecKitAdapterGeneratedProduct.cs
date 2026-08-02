using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Sockets;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

internal static class SpecKitAdapterGeneratedProduct
{
    private static readonly string[] ForbiddenRuntimeNames =
    {
        "ProgramKit", "SpecKit", "Codex", "OpenAI", "Anthropic", "prompt", "transcript",
    };

    public static void VerifyRelocatableRuntime(SpecKitAdapterPackagedWorkspace consumer)
    {
        SpecKitAdapterScenario scenario = consumer.Scenario;
        string relocated = TestRepository.CreateEmptyWorkspace();
        try
        {
            CopyDirectory(Path.Combine(consumer.Root, "products"), Path.Combine(relocated, "products"));
            CopyDirectory(Path.Combine(consumer.Root, "feeds"), Path.Combine(relocated, "feeds"));
            Assert.IsFalse(Directory.Exists(Path.Combine(relocated, ".program-kit")));
            Assert.IsFalse(Directory.Exists(Path.Combine(relocated, ".specify")));
            Assert.IsFalse(Directory.Exists(Path.Combine(relocated, "specs")));
            Assert.IsFalse(Directory.Exists(Path.Combine(relocated, "requests")));

            string app = Path.Combine(relocated, "products", scenario.ApplicationName);
            string project = scenario.ApplicationName + ".csproj";
            string packages = Path.Combine(relocated, ".runtime-packages");
            Dictionary<string, string> environment = IsolatedEnvironment(relocated, packages);
            AssertSucceeded(Run("dotnet", app, environment, "restore", project, "--locked-mode", "--configfile", "NuGet.Config", "--packages", packages, "--no-cache"));
            AssertSucceeded(Run("dotnet", app, environment, "build", project, "--configuration", "Release", "--no-restore"));
            AssertSucceeded(Run("dotnet", app, environment, "test", project, "--configuration", "Release", "--no-build", "--no-restore"));
            string publish = Path.Combine(relocated, "publish");
            AssertSucceeded(Run("dotnet", app, environment, "publish", project, "--configuration", "Release", "--no-restore", "--output", publish));
            AssertRuntimeClosure(publish);

            int port = AvailablePort();
            string applicationDll = Path.Combine(publish, scenario.ApplicationName + ".dll");
            ProcessStartInfo start = StartInfo("dotnet", publish, environment, applicationDll, "--urls", $"http://127.0.0.1:{port}");
            using Process host = Process.Start(start) ?? throw new InvalidOperationException("Could not start the relocated generated API.");
            try
            {
                JsonNode? body = null;
                using HttpClient client = new();
                for (int attempt = 0; attempt < 50; attempt++)
                {
                    try
                    {
                        body = JsonNode.Parse(client.GetStringAsync($"http://127.0.0.1:{port}{scenario.Route}").GetAwaiter().GetResult());
                        break;
                    }
                    catch (HttpRequestException)
                    {
                        Thread.Sleep(100);
                    }
                }

                Assert.IsNotNull(body);
                if (scenario == SpecKitAdapterFixture.ReferenceStatus)
                {
                    Assert.AreEqual("operational", body["state"]!.GetValue<string>());
                    Assert.AreEqual("reference.status/v1", body["contractRevision"]!.GetValue<string>());
                }
                else
                {
                    Assert.AreEqual("degraded", body["state"]!.GetValue<string>());
                    Assert.AreEqual(7, body["backorderedItems"]!.GetValue<int>());
                }
            }
            finally
            {
                if (!host.HasExited) host.Kill(entireProcessTree: true);
                host.WaitForExit();
            }
        }
        finally
        {
            TestRepository.DeleteWorkspace(relocated);
        }
    }

    private static void AssertRuntimeClosure(string publish)
    {
        JsonObject dependencies = JsonNode.Parse(File.ReadAllBytes(Directory.EnumerateFiles(publish, "*.deps.json").Single()))!.AsObject();
        string[] libraries = dependencies["libraries"]!.AsObject().Select(static item => item.Key).ToArray();
        foreach (string forbidden in ForbiddenRuntimeNames)
            Assert.IsFalse(libraries.Any(item => item.Contains(forbidden, StringComparison.OrdinalIgnoreCase)), $"Forbidden runtime library: {forbidden}");

        foreach (string assemblyPath in Directory.EnumerateFiles(publish, "*.dll", SearchOption.TopDirectoryOnly))
        {
            using FileStream stream = File.OpenRead(assemblyPath);
            using PEReader reader = new(stream);
            if (!reader.HasMetadata) continue;
            MetadataReader metadata = reader.GetMetadataReader();
            foreach (AssemblyReferenceHandle handle in metadata.AssemblyReferences)
            {
                string reference = metadata.GetString(metadata.GetAssemblyReference(handle).Name);
                foreach (string forbidden in ForbiddenRuntimeNames)
                    Assert.IsFalse(reference.Contains(forbidden, StringComparison.OrdinalIgnoreCase), $"Forbidden assembly reference {reference} in {Path.GetFileName(assemblyPath)}.");
            }
        }

        string[] forbiddenFiles = Directory.EnumerateFiles(publish, "*", SearchOption.AllDirectories)
            .Select(path => Path.GetRelativePath(publish, path).Replace('\\', '/'))
            .Where(path => path.EndsWith(".md", StringComparison.OrdinalIgnoreCase)
                || path.EndsWith(".prompt", StringComparison.OrdinalIgnoreCase)
                || path.Contains("transcript", StringComparison.OrdinalIgnoreCase)
                || path.Contains(".specify/", StringComparison.OrdinalIgnoreCase))
            .ToArray();
        Assert.AreEqual(0, forbiddenFiles.Length, string.Join(Environment.NewLine, forbiddenFiles));
    }

    private static Dictionary<string, string> IsolatedEnvironment(string root, string packages)
    {
        string home = Path.Combine(root, ".runtime-tool-home");
        Dictionary<string, string> environment = new(StringComparer.Ordinal)
        {
            ["DOTNET_CLI_HOME"] = home,
            ["NUGET_PACKAGES"] = packages,
            ["NUGET_HTTP_CACHE_PATH"] = Path.Combine(root, ".runtime-http-cache"),
            ["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1",
            ["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1",
            ["DOTNET_NOLOGO"] = "1",
            ["DOTNET_CLI_USE_MSBUILD_SERVER"] = "0",
            ["MSBUILDDISABLENODEREUSE"] = "1",
            ["NUGET_XMLDOC_MODE"] = "skip",
            ["http_proxy"] = "http://127.0.0.1:1",
            ["https_proxy"] = "http://127.0.0.1:1",
        };
        environment[OperatingSystem.IsWindows() ? "APPDATA" : "XDG_CONFIG_HOME"] = Path.Combine(root, ".runtime-config");
        return environment;
    }

    private static ProcessResult Run(string executable, string workingDirectory, IReadOnlyDictionary<string, string> environment, params string[] arguments)
    {
        using Process process = new() { StartInfo = StartInfo(executable, workingDirectory, environment, arguments) };
        process.Start();
        Task<string> output = process.StandardOutput.ReadToEndAsync();
        Task<string> error = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(120_000))
        {
            process.Kill(entireProcessTree: true);
            process.WaitForExit();
            throw new TimeoutException("Generated-product command exceeded two minutes.");
        }

        return new ProcessResult(process.ExitCode, output.GetAwaiter().GetResult(), error.GetAwaiter().GetResult());
    }

    private static ProcessStartInfo StartInfo(string executable, string workingDirectory, IReadOnlyDictionary<string, string> environment, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        foreach ((string key, string value) in environment) start.Environment[key] = value;
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        return start;
    }

    private static int AvailablePort()
    {
        using TcpListener listener = new(System.Net.IPAddress.Loopback, 0);
        listener.Start();
        return ((System.Net.IPEndPoint)listener.LocalEndpoint).Port;
    }

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source)) File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        foreach (string directory in Directory.EnumerateDirectories(source)) CopyDirectory(directory, Path.Combine(destination, Path.GetFileName(directory)));
    }

    private static void AssertSucceeded(ProcessResult result) => Assert.AreEqual(0, result.ExitCode, result.Output + result.Error);
}
