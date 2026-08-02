using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class SpecKitAdapterLifecycleAcceptanceTests
{
    private const string ExtensionId = "orbyss-program-kit-adapter";

    [TestMethod]
    [TestCategory("PlatformLifecycle")]
    [Timeout(180_000)]
    public void Real_spec_kit_lifecycle_preserves_ownership_and_rolls_back_failed_update()
    {
        string testRoot = TestRepository.CreateEmptyWorkspace();
        string workspace = Path.Combine(testRoot, "consumer");
        Directory.CreateDirectory(workspace);
        try
        {
            string packageRoot = Path.Combine(testRoot, "package");
            ProcessResult packed = Run("pwsh", TestRepository.Root, null,
                "-NoProfile", "-File", Path.Combine(TestRepository.Root, "eng", "Pack-SpecKitAdapter.ps1"),
                "-OutputRoot", packageRoot);
            AssertSucceeded(packed, "adapter package staging");
            string currentStage = Path.Combine(packageRoot, "orbyss-program-kit-adapter-0.1.0");
            string currentArchive = currentStage + ".zip";
            AssertReleaseClosure(currentStage);

            string priorStage = Path.Combine(testRoot, "prior-extension");
            CopyDirectory(currentStage, priorStage);
            Replace(Path.Combine(priorStage, "extension.yml"), "version: 0.1.0", "version: 0.0.9");
            Replace(Path.Combine(priorStage, "package-manifest.json"), "\"version\": \"0.1.0\"", "\"version\": \"0.0.9\"");
            string priorArchive = Path.Combine(testRoot, "adapter-prior.zip");
            ZipFile.CreateFromDirectory(priorStage, priorArchive, CompressionLevel.NoCompression, includeBaseDirectory: false);
            byte[] priorBytes = File.ReadAllBytes(priorArchive);

            using LocalCatalogServer catalog = new(Path.Combine(testRoot, "catalog"));
            catalog.Add("/adapter-prior.zip", "application/zip", priorBytes);
            catalog.Add("/catalog-prior.json", "application/json", Catalog(
                "0.0.9", catalog.Url("/adapter-prior.zip"), priorBytes));

            AssertSucceeded(Run("specify", workspace, null,
                "init", "--here", "--integration", "codex", "--ignore-agent-tools", "--script",
                OperatingSystem.IsWindows() ? "ps" : "sh", "--force"), "Spec Kit initialization");
            WriteCatalogConfig(workspace, catalog.Url("/catalog-prior.json"));
            AssertSucceeded(Run("specify", workspace, null,
                "extension", "add", ExtensionId), "prior adapter installation");

            string installedRoot = Path.Combine(workspace, ".specify", "extensions", ExtensionId);
            string configPath = Path.Combine(installedRoot, "orbyss-program-kit-adapter-config.yml");
            File.AppendAllText(configPath, "\nconsumerOwnedMarker: retained-exactly\n", new UTF8Encoding(false));
            byte[] consumerConfig = File.ReadAllBytes(configPath);
            Dictionary<string, byte[]> protectedArtifacts = WriteProtectedArtifacts(workspace);

            catalog.Add("/adapter-current.zip", "application/zip", File.ReadAllBytes(currentArchive));
            catalog.Add("/catalog-current.json", "application/json", Catalog(
                "0.1.0", catalog.Url("/adapter-current.zip"), File.ReadAllBytes(currentArchive)));
            WriteCatalogConfig(workspace, catalog.Url("/catalog-current.json"));

            ProcessResult updated = Run("specify", workspace, "y\n",
                "extension", "update", ExtensionId);
            AssertSucceeded(updated, "compatible adapter update");
            Assert.AreEqual("0.1.0", InstalledVersion(installedRoot));
            CollectionAssert.AreEqual(consumerConfig, File.ReadAllBytes(configPath));
            AssertProtectedArtifacts(workspace, protectedArtifacts);

            InitializeCleanGitRepository(workspace);
            byte[] registrationBeforeUpgrade = File.ReadAllBytes(Path.Combine(workspace, ".specify", "extensions.yml"));
            string integrity = Path.Combine(workspace, "integrity.ps1");
            File.WriteAllText(integrity, "$global:LASTEXITCODE = 0\n", new UTF8Encoding(false));
            CommitAll(workspace, "add upgrade integrity fixture");
            ProcessResult upgraded = Run("pwsh", TestRepository.Root, null,
                "-NoProfile", "-File", Path.Combine(TestRepository.Root, "eng", "Invoke-SpecKitUpgrade.ps1"),
                "-Mode", "Upgrade", "-RepositoryRoot", workspace, "-SpecifyCommand", "specify",
                "-IntegrityScript", integrity, "-Workflow", "");
            AssertSucceeded(upgraded, "manifest-aware Spec Kit upgrade");
            CollectionAssert.AreEqual(registrationBeforeUpgrade, File.ReadAllBytes(Path.Combine(workspace, ".specify", "extensions.yml")));
            CollectionAssert.AreEqual(consumerConfig, File.ReadAllBytes(configPath));
            AssertProtectedArtifacts(workspace, protectedArtifacts);

            string incompatibleStage = Path.Combine(testRoot, "incompatible-extension");
            CopyDirectory(currentStage, incompatibleStage);
            Replace(Path.Combine(incompatibleStage, "extension.yml"), "version: 0.1.0", "version: 0.2.0");
            Replace(Path.Combine(incompatibleStage, "extension.yml"), "speckit_version: \"==0.15.1\"", "speckit_version: \"==99.0.0\"");
            string incompatibleArchive = Path.Combine(testRoot, "adapter-incompatible.zip");
            ZipFile.CreateFromDirectory(incompatibleStage, incompatibleArchive, CompressionLevel.NoCompression, includeBaseDirectory: false);
            byte[] incompatibleBytes = File.ReadAllBytes(incompatibleArchive);
            catalog.Add("/adapter-incompatible.zip", "application/zip", incompatibleBytes);
            catalog.Add("/catalog-incompatible.json", "application/json", Catalog(
                "0.2.0", catalog.Url("/adapter-incompatible.zip"), incompatibleBytes));
            WriteCatalogConfig(workspace, catalog.Url("/catalog-incompatible.json"));
            string releaseBeforeFailure = TestRepository.DigestTree(installedRoot);
            ProcessResult failedUpdate = Run("specify", workspace, "y\n",
                "extension", "update", ExtensionId);
            Assert.AreNotEqual(0, failedUpdate.ExitCode, failedUpdate.StandardOutput + failedUpdate.StandardError);
            Assert.AreEqual(releaseBeforeFailure, TestRepository.DigestTree(installedRoot));
            Assert.AreEqual("0.1.0", InstalledVersion(installedRoot));
            CollectionAssert.AreEqual(consumerConfig, File.ReadAllBytes(configPath));
            AssertProtectedArtifacts(workspace, protectedArtifacts);

            AssertSucceeded(Run("specify", workspace, null, "extension", "disable", ExtensionId), "adapter disable");
            CollectionAssert.AreEqual(consumerConfig, File.ReadAllBytes(configPath));
            AssertProtectedArtifacts(workspace, protectedArtifacts);
            AssertSucceeded(Run("specify", workspace, null, "extension", "enable", ExtensionId), "adapter enable");
            CollectionAssert.AreEqual(consumerConfig, File.ReadAllBytes(configPath));
            AssertProtectedArtifacts(workspace, protectedArtifacts);

            string requestPath = Path.Combine(workspace, "doctor-request.json");
            File.WriteAllText(requestPath,
                "{\"schema\":\"program-kit.spec-kit-adapter-request/v1\",\"operation\":\"doctor\",\"workspace\":{},\"config\":{\"logicalPath\":\".specify/extensions/orbyss-program-kit-adapter/orbyss-program-kit-adapter-config.yml\"},\"requestedEffect\":\"none\",\"outputRoot\":\"specs/base/program-kit/generated\"}",
                new UTF8Encoding(false));
            string installedAdapter = Path.Combine(installedRoot, "tools", "program-kit-spec-kit-adapter.dll");
            string beforeRevalidation = DigestProtectedArtifacts(workspace, protectedArtifacts.Keys);
            ProcessResult revalidated = Run("dotnet", workspace, null, installedAdapter, "doctor",
                "--workspace", workspace, "--request", requestPath, "--format", "json");
            Assert.AreNotEqual(0, revalidated.ExitCode, "Re-enable must not silently resume without validation.");
            JsonObject revalidation = JsonNode.Parse(revalidated.StandardOutput)!.AsObject();
            Assert.AreNotEqual("succeeded", revalidation["outcome"]!.GetValue<string>());
            Assert.AreEqual(beforeRevalidation, DigestProtectedArtifacts(workspace, protectedArtifacts.Keys));

            AssertSucceeded(Run("specify", workspace, null,
                "extension", "remove", ExtensionId, "--keep-config", "--force"), "adapter removal with config preservation");
            Assert.IsTrue(File.Exists(configPath));
            CollectionAssert.AreEqual(consumerConfig, File.ReadAllBytes(configPath));
            Assert.IsTrue(File.Exists(Path.Combine(installedRoot, ".keep-config")));
            Assert.IsFalse(File.Exists(Path.Combine(installedRoot, "extension.yml")));
            Assert.IsFalse(File.Exists(installedAdapter));
            Assert.IsFalse(File.ReadAllText(Path.Combine(workspace, ".specify", "extensions.yml")).Contains(ExtensionId, StringComparison.Ordinal));
            AssertProtectedArtifacts(workspace, protectedArtifacts);
        }
        finally
        {
            DeleteLifecycleRoot(testRoot);
        }
    }

    private static void DeleteLifecycleRoot(string root)
    {
        if (Directory.Exists(root))
        {
            foreach (string file in Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories))
            {
                if ((File.GetAttributes(file) & FileAttributes.ReparsePoint) == 0) File.SetAttributes(file, FileAttributes.Normal);
            }
        }

        TestRepository.DeleteWorkspace(root);
    }

    private static void AssertReleaseClosure(string stageRoot)
    {
        JsonObject package = JsonNode.Parse(File.ReadAllText(Path.Combine(stageRoot, "package-manifest.json")))!.AsObject();
        Assert.AreEqual("consumer-owned", package["ownership"]!["projectConfig"]!.GetValue<string>());
        Assert.AreEqual("spec-kit-managed", package["ownership"]!["registration"]!.GetValue<string>());
        Assert.AreEqual("specify extension remove orbyss-program-kit-adapter --keep-config", package["lifecycle"]!["remove"]!.GetValue<string>());
        JsonObject release = JsonNode.Parse(File.ReadAllText(Path.Combine(stageRoot, "release-files.json")))!.AsObject();
        string[] actual = Directory.EnumerateFiles(stageRoot, "*", SearchOption.AllDirectories)
            .Select(path => Path.GetRelativePath(stageRoot, path).Replace('\\', '/'))
            .Where(path => path != "release-files.json")
            .OrderBy(path => path, StringComparer.Ordinal)
            .ToArray();
        JsonObject[] declared = release["files"]!.AsArray().OfType<JsonObject>().ToArray();
        CollectionAssert.AreEquivalent(actual, declared.Select(item => item["logicalPath"]!.GetValue<string>()).ToArray());
        foreach (JsonObject item in declared)
        {
            string logicalPath = item["logicalPath"]!.GetValue<string>();
            Assert.AreEqual(Digest(File.ReadAllBytes(Path.Combine(stageRoot, logicalPath.Replace('/', Path.DirectorySeparatorChar)))), item["digest"]!.GetValue<string>());
        }
    }

    private static Dictionary<string, byte[]> WriteProtectedArtifacts(string workspace)
    {
        Dictionary<string, string> content = new(StringComparer.Ordinal)
        {
            [".config/dotnet-tools.json"] = "consumer tool declaration",
            [".program-kit/state.json"] = "program kit state",
            ["specs/003-lifecycle/program-kit/handoff.yaml"] = "consumer handoff",
            ["specs/003-lifecycle/program-kit/handoff-review.json"] = "consumer review",
            ["specs/003-lifecycle/program-kit/generated/results/prepare.json"] = "retained adapter result",
            ["products/reference-status/receipt.json"] = "program kit receipt",
            ["src/Consumer.cs"] = "consumer source",
        };
        Dictionary<string, byte[]> result = new(StringComparer.Ordinal);
        foreach ((string logicalPath, string value) in content)
        {
            string path = Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            byte[] bytes = Encoding.UTF8.GetBytes(value);
            File.WriteAllBytes(path, bytes);
            result[logicalPath] = bytes;
        }

        return result;
    }

    private static void AssertProtectedArtifacts(string workspace, IReadOnlyDictionary<string, byte[]> expected)
    {
        foreach ((string logicalPath, byte[] bytes) in expected)
        {
            string path = Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            Assert.IsTrue(File.Exists(path), logicalPath);
            CollectionAssert.AreEqual(bytes, File.ReadAllBytes(path), logicalPath);
        }
    }

    private static string DigestProtectedArtifacts(string workspace, IEnumerable<string> logicalPaths) => string.Join('\n', logicalPaths
        .OrderBy(path => path, StringComparer.Ordinal)
        .Select(path => $"{path}:{Digest(File.ReadAllBytes(Path.Combine(workspace, path.Replace('/', Path.DirectorySeparatorChar))))}"));

    private static void InitializeCleanGitRepository(string workspace)
    {
        if (!Directory.Exists(Path.Combine(workspace, ".git"))) AssertSucceeded(Run("git", workspace, null, "init"), "git initialization");
        AssertSucceeded(Run("git", workspace, null, "config", "user.email", "lifecycle-proof@program-kit.invalid"), "git email configuration");
        AssertSucceeded(Run("git", workspace, null, "config", "user.name", "Program Kit Lifecycle Proof"), "git name configuration");
        CommitAll(workspace, "record lifecycle fixture");
    }

    private static void CommitAll(string workspace, string message)
    {
        AssertSucceeded(Run("git", workspace, null, "add", "."), "git staging");
        AssertSucceeded(Run("git", workspace, null, "commit", "-m", message), "git commit");
    }

    private static void WriteCatalogConfig(string workspace, string url)
    {
        File.WriteAllText(Path.Combine(workspace, ".specify", "extension-catalogs.yml"),
            $"catalogs:\n  - name: lifecycle-proof\n    url: {url}\n    priority: 1\n    install_allowed: true\n",
            new UTF8Encoding(false));
    }

    private static byte[] Catalog(string version, string downloadUrl, byte[] archive) => Encoding.UTF8.GetBytes(
        $"{{\"schema_version\":\"1.0\",\"extensions\":{{\"{ExtensionId}\":{{\"name\":\"Program Kit Adapter\",\"version\":\"{version}\",\"description\":\"Lifecycle fixture\",\"download_url\":\"{downloadUrl}\",\"sha256\":\"{Digest(archive)[7..]}\"}}}}}}");

    private static string InstalledVersion(string installedRoot)
    {
        JsonObject manifest = Orbyss.ProgramKit.SpecKitAdapter.Contracts.RestrictedYaml.Parse(File.ReadAllText(Path.Combine(installedRoot, "extension.yml")));
        return manifest["extension"]!["version"]!.GetValue<string>();
    }

    private static void Replace(string path, string oldValue, string newValue)
    {
        string text = File.ReadAllText(path);
        Assert.IsTrue(text.Contains(oldValue, StringComparison.Ordinal), path);
        File.WriteAllText(path, text.Replace(oldValue, newValue, StringComparison.Ordinal), new UTF8Encoding(false));
    }

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (string file in Directory.EnumerateFiles(source)) File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        foreach (string directory in Directory.EnumerateDirectories(source)) CopyDirectory(directory, Path.Combine(destination, Path.GetFileName(directory)));
    }

    private static string Digest(byte[] bytes) => "sha256:" + Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();

    private static void AssertSucceeded(ProcessResult result, string operation) =>
        Assert.AreEqual(0, result.ExitCode, $"{operation} failed.\nstdout:\n{result.StandardOutput}\nstderr:\n{result.StandardError}");

    private static ProcessResult Run(string executable, string workingDirectory, string? standardInput, params string[] arguments)
    {
        ProcessStartInfo start = new(executable)
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            RedirectStandardInput = standardInput is not null,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        start.Environment["NO_COLOR"] = "1";
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException($"Unable to start {executable}.");
        if (standardInput is not null)
        {
            process.StandardInput.Write(standardInput);
            process.StandardInput.Close();
        }

        var stdout = process.StandardOutput.ReadToEndAsync();
        var stderr = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(120_000))
        {
            process.Kill(entireProcessTree: true);
            throw new TimeoutException($"{executable} did not complete within two minutes.");
        }

        return new ProcessResult(process.ExitCode, stdout.GetAwaiter().GetResult(), stderr.GetAwaiter().GetResult());
    }

    private sealed record ProcessResult(int ExitCode, string StandardOutput, string StandardError);

    private sealed class LocalCatalogServer : IDisposable
    {
        private readonly string root;
        private readonly int port;
        private readonly Process process;

        public LocalCatalogServer(string root)
        {
            this.root = root;
            Directory.CreateDirectory(root);
            using (TcpListener portProbe = new(IPAddress.Loopback, 0))
            {
                portProbe.Start();
                port = ((IPEndPoint)portProbe.LocalEndpoint).Port;
            }

            ProcessStartInfo start = new(OperatingSystem.IsWindows() ? "python" : "python3")
            {
                WorkingDirectory = root,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            foreach (string argument in new[] { "-m", "http.server", port.ToString(System.Globalization.CultureInfo.InvariantCulture), "--bind", "127.0.0.1", "--directory", root })
                start.ArgumentList.Add(argument);
            process = Process.Start(start) ?? throw new InvalidOperationException("Unable to start the lifecycle catalog server.");
            Stopwatch ready = Stopwatch.StartNew();
            while (ready.Elapsed < TimeSpan.FromSeconds(5))
            {
                try
                {
                    using TcpClient probe = new();
                    probe.Connect(IPAddress.Loopback, port);
                    return;
                }
                catch (SocketException)
                {
                    if (process.HasExited) throw new InvalidOperationException("The lifecycle catalog server exited before accepting requests.");
                    Thread.Sleep(50);
                }
            }

            throw new TimeoutException("The lifecycle catalog server did not become ready.");
        }

        public string Url(string path) => $"http://127.0.0.1:{port}{path}";

        public void Add(string path, string contentType, byte[] bytes)
        {
            _ = contentType;
            string destination = Path.Combine(root, path.TrimStart('/').Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
            File.WriteAllBytes(destination, bytes);
        }

        public void Dispose()
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                process.WaitForExit(5_000);
            }
            process.Dispose();
        }
    }
}
