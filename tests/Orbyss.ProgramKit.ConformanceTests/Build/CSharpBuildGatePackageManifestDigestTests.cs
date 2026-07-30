using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
public sealed class CSharpBuildGatePackageManifestDigestTests
{
    private const string Algorithm = "sha256(path-utf8,0,file-bytes,0)";

    [TestMethod]
    [DataRow(
        "authoring-package-manifest.json",
        "sourceInventory")]
    [DataRow(
        "build-package-manifest.json",
        "sourceInventory")]
    [DataRow(
        "testing-package-manifest.json",
        "sourceInventory")]
    [DataRow(
        "testing-package-manifest.json",
        "operationSourceInventory")]
    public void InventoryDigestUsesGitNormalizedIndexBytes(
        string manifestName,
        string inventoryName)
    {
        var manifestPath = Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "extensions",
            "reusable-csharp-build-gates",
            manifestName);
        using var manifest = JsonDocument.Parse(
            File.ReadAllBytes(manifestPath));
        var inventory = manifest.RootElement.GetProperty(inventoryName);
        Assert.AreEqual(
            Algorithm,
            inventory.GetProperty("digestAlgorithm").GetString());
        var paths = inventory.GetProperty("paths")
            .EnumerateArray()
            .Select(element => element.GetString()
                ?? throw new InvalidOperationException(
                    "Inventory paths cannot be null."))
            .ToArray();
        Assert.AreSequenceEqual(
            paths.Order(StringComparer.Ordinal),
            paths);
        Assert.HasCount(
            paths.Length,
            paths.Distinct(StringComparer.Ordinal));

        using var hash = IncrementalHash.CreateHash(
            HashAlgorithmName.SHA256);
        foreach (var path in paths)
        {
            hash.AppendData(Encoding.UTF8.GetBytes(path));
            hash.AppendData([0]);
            hash.AppendData(ReadGitIndexBytes(path));
            hash.AppendData([0]);
        }

        var actual = string.Concat(
            "sha256:",
            Convert.ToHexStringLower(hash.GetHashAndReset()));
        Assert.AreEqual(
            inventory.GetProperty("digest").GetString(),
            actual);
    }

    private static byte[] ReadGitIndexBytes(string relativePath)
    {
        Assert.IsFalse(Path.IsPathRooted(relativePath));
        Assert.DoesNotContain('\\', relativePath);
        Assert.IsEmpty(relativePath
            .Split('/')
            .Where(segment => segment is "" or "." or "..")
            .ToArray());

        ProcessStartInfo startInfo = new("git")
        {
            WorkingDirectory = ConformanceInputs.ProgramKitRoot,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        startInfo.ArgumentList.Add("-c");
        startInfo.ArgumentList.Add(string.Concat(
            "safe.directory=",
            ConformanceInputs.ProgramKitRoot.Replace('\\', '/')));
        startInfo.ArgumentList.Add("-C");
        startInfo.ArgumentList.Add(ConformanceInputs.ProgramKitRoot);
        startInfo.ArgumentList.Add("show");
        startInfo.ArgumentList.Add("--no-ext-diff");
        startInfo.ArgumentList.Add("--no-textconv");
        startInfo.ArgumentList.Add(string.Concat(":", relativePath));

        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException(
                "Could not start Git for source inventory verification.");
        using MemoryStream output = new();
        var copyOutput = process.StandardOutput.BaseStream.CopyToAsync(output);
        var readError = process.StandardError.ReadToEndAsync();
        process.WaitForExit();
        Task.WaitAll(copyOutput, readError);
        Assert.AreEqual(
            0,
            process.ExitCode,
            string.Concat(
                "Git could not read normalized index bytes for '",
                relativePath,
                "'.",
                Environment.NewLine,
                readError.Result));
        return output.ToArray();
    }
}
