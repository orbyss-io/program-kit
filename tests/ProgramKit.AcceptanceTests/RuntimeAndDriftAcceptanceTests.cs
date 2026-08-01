using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Runtime.InteropServices;
using System.Text.Json.Nodes;
using System.Threading;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class RuntimeAndDriftAcceptanceTests
{
    [TestMethod]
    public void GeneratedHostRunsFromCleanRelocationWithAllowlistedDependencies()
    {
        string workspace = ConstructWorkspace();
        string relocated = Path.Combine(Path.GetTempPath(), "program-kit-tests", Guid.NewGuid().ToString("N"));
        try
        {
            CopyDirectory(Path.Combine(workspace, "products"), Path.Combine(relocated, "products"));
            CopyDirectory(Path.Combine(workspace, "feeds"), Path.Combine(relocated, "feeds"));
            Assert.IsFalse(Directory.Exists(Path.Combine(relocated, ".program-kit")));
            Assert.IsFalse(Directory.Exists(Path.Combine(relocated, "requests")));
            Assert.IsFalse(Directory.Exists(Path.Combine(relocated, "authority")));
            Assert.IsFalse(Directory.Exists(Path.Combine(relocated, "definitions")));

            string app = Path.Combine(relocated, "products", "Reference.Status.Api");
            string packages = Path.Combine(relocated, ".runtime-packages");
            string toolHome = Path.Combine(relocated, ".tool-home");
            Assert.IsFalse(Directory.Exists(packages));
            Assert.IsFalse(Directory.Exists(toolHome));

            ProcessResult restore = Run(
                "dotnet", app, toolHome, packages,
                "restore", "Reference.Status.Api.csproj", "--locked-mode", "--configfile", "NuGet.Config", "--packages", packages, "--no-cache");
            Assert.AreEqual(0, restore.ExitCode, restore.Output);
            AssertPackageAssetAllowlist(relocated, app, packages);

            ProcessResult build = Run(
                "dotnet", app, toolHome, packages,
                "build", "Reference.Status.Api.csproj", "--configuration", "Release", "--no-restore");
            Assert.AreEqual(0, build.ExitCode, build.Output);
            ProcessResult test = Run(
                "dotnet", app, toolHome, packages,
                "test", "Reference.Status.Api.csproj", "--configuration", "Release", "--no-build", "--no-restore");
            Assert.AreEqual(0, test.ExitCode, test.Output);

            string publish = Path.Combine(relocated, "publish");
            ProcessResult publication = Run(
                "dotnet", app, toolHome, packages,
                "publish", "Reference.Status.Api.csproj", "--configuration", "Release", "--no-restore", "--output", publish);
            Assert.AreEqual(0, publication.ExitCode, publication.Output);
            AssertDependencyContextAllowlist(relocated, publish);
            AssertPortableExecutableReferenceAllowlist(publish);

            int port = AvailablePort();
            ProcessStartInfo start = StartInfo(
                "dotnet", publish, toolHome, packages,
                Path.Combine(publish, "Reference.Status.Api.dll"), "--urls", $"http://127.0.0.1:{port}");
            using Process process = Process.Start(start) ?? throw new InvalidOperationException("Unable to start generated host.");
            try
            {
                using HttpClient client = new();
                string? body = null;
                for (int attempt = 0; attempt < 50; attempt++)
                {
                    try
                    {
                        body = client.GetStringAsync($"http://127.0.0.1:{port}/status").GetAwaiter().GetResult();
                        break;
                    }
                    catch (HttpRequestException)
                    {
                        Thread.Sleep(100);
                    }
                }

                Assert.IsNotNull(body);
                Assert.AreEqual("operational", JsonNode.Parse(body)!["state"]!.GetValue<string>());
            }
            finally
            {
                if (!process.HasExited)
                {
                    process.Kill(entireProcessTree: true);
                }

                process.WaitForExit();
            }
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
            TestRepository.DeleteWorkspace(relocated);
        }
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
            JsonNode result = JsonNode.Parse(evaluate.StandardOutput)!;
            string[] ids = result["diagnostics"]!["items"]!.AsArray().Select(item => item!["id"]!.GetValue<string>()).ToArray();
            ContractAssertions.AssertValid(ContractAssertions.OperationResult, result.AsObject());
            JsonObject fixture = JsonNode.Parse(File.ReadAllBytes(TestRepository.Fixture("Invalid/GeneratedDrift/fixture.json")))!.AsObject();
            CollectionAssert.Contains(ids, fixture["expectedDiagnostic"]!.GetValue<string>());
            Assert.AreEqual(fixture["expectedOutcome"]!.GetValue<string>(), result["outcome"]!.GetValue<string>());
            Assert.AreEqual(fixture["expectedEffectState"]!.GetValue<string>(), result["effectState"]!.GetValue<string>());
            Assert.AreEqual(fixture["expectedDisposition"]!.GetValue<string>(), result["primaryDisposition"]!.GetValue<string>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static void AssertPackageAssetAllowlist(string relocated, string app, string packagesRoot)
    {
        JsonObject assets = JsonNode.Parse(File.ReadAllBytes(Path.Combine(app, "obj", "project.assets.json")))!.AsObject();
        HashSet<string> allowed = GovernedPackageAllowlist(relocated);
        HashSet<string> actual = assets["libraries"]!.AsObject()
            .Where(static item => item.Value!["type"]!.GetValue<string>() == "package")
            .Select(static item => item.Key)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        string[] unexpected = actual.Except(allowed, StringComparer.OrdinalIgnoreCase).OrderBy(static item => item, StringComparer.Ordinal).ToArray();
        Assert.AreEqual(0, unexpected.Length, $"Unexpected assets packages:{Environment.NewLine}{string.Join(Environment.NewLine, unexpected)}");
        Assert.IsTrue(actual.Contains("Reference.Status/1.0.0"));
        Assert.IsTrue(actual.Contains("CShells.AspNetCore/0.0.28"));

        string expectedPackages = Path.GetFullPath(packagesRoot).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        string[] packageFolders = assets["packageFolders"]!.AsObject().Select(static item => item.Key).ToArray();
        Assert.AreEqual(1, packageFolders.Length);
        Assert.AreEqual(
            expectedPackages,
            Path.GetFullPath(packageFolders[0]).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
            StringComparer.OrdinalIgnoreCase);

        string[] sources = assets["project"]!["restore"]!["sources"]!.AsObject().Select(static item => item.Key).ToArray();
        string[] expectedSources =
        {
            Path.GetFullPath(Path.Combine(relocated, "feeds", "component")),
            Path.GetFullPath(Path.Combine(relocated, "feeds", "dependencies")),
            DotNetLibraryPacksRoot(),
        };
        CollectionAssert.AreEquivalent(
            expectedSources.Select(static path => path.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)).ToArray(),
            sources.Select(static path => Path.GetFullPath(path).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)).ToArray(),
            string.Join(Environment.NewLine, sources));
    }

    private static void AssertDependencyContextAllowlist(string relocated, string publish)
    {
        JsonObject dependencies = JsonNode.Parse(File.ReadAllBytes(Path.Combine(publish, "Reference.Status.Api.deps.json")))!.AsObject();
        HashSet<string> allowed = GovernedPackageAllowlist(relocated);
        allowed.Add("Reference.Status.Api/1.0.0");
        HashSet<string> actual = dependencies["libraries"]!.AsObject().Select(static item => item.Key).ToHashSet(StringComparer.OrdinalIgnoreCase);
        string[] unexpected = actual.Except(allowed, StringComparer.OrdinalIgnoreCase).OrderBy(static item => item, StringComparer.Ordinal).ToArray();
        Assert.AreEqual(0, unexpected.Length, $"Unexpected deps libraries:{Environment.NewLine}{string.Join(Environment.NewLine, unexpected)}");
        Assert.IsTrue(actual.Contains("Reference.Status.Api/1.0.0"));
        Assert.IsTrue(actual.Contains("Reference.Status/1.0.0"));
    }

    private static void AssertPortableExecutableReferenceAllowlist(string publish)
    {
        HashSet<string> allowed = Directory.EnumerateFiles(publish, "*.dll", SearchOption.TopDirectoryOnly)
            .Select(Path.GetFileNameWithoutExtension)
            .ToHashSet(StringComparer.OrdinalIgnoreCase)!;
        allowed.UnionWith(SharedFrameworkAssemblies(publish));

        List<string> unexpected = new();
        int inspected = 0;
        foreach (string assemblyPath in Directory.EnumerateFiles(publish, "*.dll", SearchOption.TopDirectoryOnly).OrderBy(static path => path, StringComparer.Ordinal))
        {
            using FileStream stream = File.OpenRead(assemblyPath);
            using PEReader pe = new(stream);
            if (!pe.HasMetadata)
            {
                continue;
            }

            MetadataReader metadata = pe.GetMetadataReader();
            if (!metadata.IsAssembly)
            {
                continue;
            }

            inspected++;
            foreach (AssemblyReferenceHandle handle in metadata.AssemblyReferences)
            {
                string reference = metadata.GetString(metadata.GetAssemblyReference(handle).Name);
                if (!allowed.Contains(reference))
                {
                    unexpected.Add($"{Path.GetFileName(assemblyPath)} -> {reference}");
                }
            }
        }

        Assert.IsTrue(inspected > 0);
        Assert.AreEqual(0, unexpected.Count, $"Unexpected PE references:{Environment.NewLine}{string.Join(Environment.NewLine, unexpected)}");
        Assert.IsFalse(allowed.Any(static name => name.Contains("ProgramKit", StringComparison.OrdinalIgnoreCase)
            || name.Contains("SpecKit", StringComparison.OrdinalIgnoreCase)
            || name.Contains("OpenAI", StringComparison.OrdinalIgnoreCase)));
    }

    private static HashSet<string> SharedFrameworkAssemblies(string publish)
    {
        JsonObject runtime = JsonNode.Parse(File.ReadAllBytes(Path.Combine(publish, "Reference.Status.Api.runtimeconfig.json")))!.AsObject();
        JsonObject options = runtime["runtimeOptions"]!.AsObject();
        IEnumerable<JsonObject> frameworks = options["frameworks"] is JsonArray array
            ? array.OfType<JsonObject>()
            : options["framework"] is JsonObject single ? new[] { single } : Array.Empty<JsonObject>();
        DirectoryInfo runtimeDirectory = new(RuntimeEnvironment.GetRuntimeDirectory().TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar));
        DirectoryInfo sharedRoot = runtimeDirectory.Parent?.Parent
            ?? throw new InvalidOperationException("The selected .NET shared-framework root is unavailable.");
        HashSet<string> assemblies = new(StringComparer.OrdinalIgnoreCase);
        foreach (JsonObject framework in frameworks)
        {
            string name = framework["name"]!.GetValue<string>();
            Version requested = Version.Parse(framework["version"]!.GetValue<string>());
            string frameworkRoot = Path.Combine(sharedRoot.FullName, name);
            string selected = Directory.EnumerateDirectories(frameworkRoot)
                .Select(static path => (Path: path, Name: Path.GetFileName(path)))
                .Where(item => Version.TryParse(item.Name, out Version? parsed)
                    && parsed.Major == requested.Major
                    && parsed.Minor == requested.Minor
                    && parsed >= requested)
                .OrderByDescending(item => Version.Parse(item.Name))
                .Select(static item => item.Path)
                .FirstOrDefault()
                ?? throw new InvalidOperationException($"The declared shared framework is unavailable: {name}/{requested}");
            assemblies.UnionWith(Directory.EnumerateFiles(selected, "*.dll", SearchOption.TopDirectoryOnly).Select(Path.GetFileNameWithoutExtension)!);
        }

        return assemblies;
    }

    private static HashSet<string> GovernedPackageAllowlist(string relocated)
    {
        JsonObject mirror = JsonNode.Parse(File.ReadAllBytes(Path.Combine(relocated, "feeds", "dependencies", "mirror.lock.json")))!.AsObject();
        HashSet<string> allowed = mirror["packages"]!.AsArray().OfType<JsonObject>()
            .Select(static package => $"{package["id"]!.GetValue<string>()}/{package["version"]!.GetValue<string>()}")
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        allowed.Add("Reference.Status/1.0.0");
        return allowed;
    }

    private static string DotNetLibraryPacksRoot()
    {
        DirectoryInfo runtimeDirectory = new(RuntimeEnvironment.GetRuntimeDirectory().TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar));
        DirectoryInfo dotnetRoot = runtimeDirectory.Parent?.Parent?.Parent
            ?? throw new InvalidOperationException("The selected .NET installation root is unavailable.");
        return Path.Combine(dotnetRoot.FullName, "library-packs");
    }

    private static string ConstructWorkspace()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        var construct = TestRepository.RunCli("construct", "--workspace", workspace, "--request", Path.Combine(workspace, "requests", "construct.json"), "--format", "json");
        if (construct.ExitCode != 0)
        {
            TestRepository.DeleteWorkspace(workspace);
            Assert.Fail(construct.StandardOutput + construct.StandardError);
        }

        return workspace;
    }

    private static ProcessResult Run(
        string executable,
        string workingDirectory,
        string toolHome,
        string packagesRoot,
        params string[] arguments)
    {
        using Process process = Process.Start(StartInfo(executable, workingDirectory, toolHome, packagesRoot, arguments))
            ?? throw new InvalidOperationException("Unable to start child process.");
        string output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd();
        process.WaitForExit();
        return new ProcessResult(process.ExitCode, output);
    }

    private static ProcessStartInfo StartInfo(
        string executable,
        string workingDirectory,
        string toolHome,
        string packagesRoot,
        params string[] arguments)
    {
        Directory.CreateDirectory(toolHome);
        ProcessStartInfo start = new(executable)
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (string argument in arguments)
        {
            start.ArgumentList.Add(argument);
        }

        start.Environment["DOTNET_CLI_HOME"] = toolHome;
        start.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        start.Environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1";
        start.Environment["DOTNET_NOLOGO"] = "1";
        start.Environment["DOTNET_CLI_UI_LANGUAGE"] = "en-US";
        start.Environment["NUGET_PACKAGES"] = packagesRoot;
        start.Environment["NUGET_XMLDOC_MODE"] = "skip";
        if (OperatingSystem.IsWindows())
        {
            start.Environment["APPDATA"] = toolHome;
        }
        else
        {
            start.Environment["XDG_CONFIG_HOME"] = toolHome;
            start.Environment["LANG"] = "C";
            start.Environment["LC_ALL"] = "C";
        }

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

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source))
        {
            File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        }

        foreach (string directory in Directory.EnumerateDirectories(source))
        {
            CopyDirectory(directory, Path.Combine(destination, Path.GetFileName(directory)));
        }
    }

    private sealed record ProcessResult(int ExitCode, string Output);
}
