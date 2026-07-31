using System.Diagnostics;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.ConformanceTests.Infrastructure;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
[DoNotParallelize]
public sealed class CSharpBuildGateTestingIntegrationTests
{
    [TestMethod]
    public void TestingPackageHasNoAnalyzerBuildOrRuntimeAssets()
    {
        var output = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-csharp-gate-testing-pack-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(output);
        try
        {
            var project = Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                "src",
                "Orbyss.ProgramKit.CSharpBuildGates.Testing",
                "Orbyss.ProgramKit.CSharpBuildGates.Testing.csproj");
            var result = Run(
                ConformanceInputs.ProgramKitRoot,
                "pack",
                project,
                "--no-restore",
                "--configuration",
                "Debug",
                "--output",
                output);
            Assert.AreEqual(0, result.ExitCode, result.Output);

            var package = Directory.EnumerateFiles(output, "*.nupkg").Single();
            using var archive = ZipFile.OpenRead(package);
            var entries = archive.Entries
                .Select(entry => entry.FullName.Replace('\\', '/'))
                .ToArray();
            Assert.Contains(
                "lib/net10.0/Orbyss.ProgramKit.CSharpBuildGates.Testing.dll",
                entries);
            Assert.Contains("README.md", entries);
            Assert.IsEmpty(entries.Where(entry =>
                entry.StartsWith("analyzers/", StringComparison.OrdinalIgnoreCase) ||
                entry.StartsWith("build/", StringComparison.OrdinalIgnoreCase) ||
                entry.StartsWith(
                    "buildTransitive/",
                    StringComparison.OrdinalIgnoreCase) ||
                entry.StartsWith("runtime/", StringComparison.OrdinalIgnoreCase) ||
                entry.StartsWith("runtimes/", StringComparison.OrdinalIgnoreCase))
                .ToArray());
        }
        finally
        {
            if (Directory.Exists(output))
            {
                Directory.Delete(output, recursive: true);
            }
        }
    }

    [TestMethod]
    public void TestingManifestBindsPackageOperationsAndVersionMap()
    {
        var manifestPath = Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            ".review-sets",
            "reusable-csharp-build-gates",
            "testing-package-manifest.json");
        using var manifest = JsonDocument.Parse(File.ReadAllBytes(manifestPath));
        AssertInventory(manifest.RootElement.GetProperty("sourceInventory"));
        AssertInventory(
            manifest.RootElement.GetProperty("operationSourceInventory"));

        var manifestDigest = string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(
                File.ReadAllBytes(manifestPath))));
        var versionMap = File.ReadAllText(Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            ".review-sets",
            "reusable-csharp-build-gates",
            "testing-version-map.json"));
        Assert.Contains(manifestDigest, versionMap);
        Assert.Contains(
            "\"identity\": \"pkid:command-line:program-kit:csharp-build-gate-operations\"",
            versionMap);
        Assert.Contains(
            "\"identity\": \"pkid:package:program-kit:csharp-build-gates-testing\"",
            versionMap);
    }

    private static void AssertInventory(JsonElement inventory)
    {
        var paths = inventory.GetProperty("paths")
            .EnumerateArray()
            .Select(element => element.GetString()
                ?? throw new InvalidOperationException(
                    "Inventory paths cannot be null."))
            .ToArray();
        Assert.AreSequenceEqual(paths.Order(StringComparer.Ordinal), paths);
        Assert.HasCount(
            paths.Length,
            paths.Distinct(StringComparer.Ordinal));

        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var path in paths)
        {
            hash.AppendData(Encoding.UTF8.GetBytes(path));
            hash.AppendData([0]);
            hash.AppendData(File.ReadAllBytes(Path.Combine(
                ConformanceInputs.ProgramKitRoot,
                path.Replace('/', Path.DirectorySeparatorChar))));
            hash.AppendData([0]);
        }

        Assert.AreEqual(
            inventory.GetProperty("digest").GetString(),
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(hash.GetHashAndReset())));
    }

    private static (int ExitCode, string Output) Run(
        string workingDirectory,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start dotnet.");
        var output = process.StandardOutput.ReadToEndAsync();
        var error = process.StandardError.ReadToEndAsync();
        process.WaitForExit();
        Task.WaitAll(output, error);
        return (
            process.ExitCode,
            string.Concat(output.Result, Environment.NewLine, error.Result));
    }
}
