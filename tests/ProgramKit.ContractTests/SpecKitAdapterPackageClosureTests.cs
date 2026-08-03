using System;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using System.Xml.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
[DoNotParallelize]
public sealed class SpecKitAdapterPackageClosureTests
{
    [TestMethod]
    public void Extension_archive_is_deterministic_complete_inspectable_and_public_contract_only()
    {
        string root = TestRepository.CreateEmptyWorkspace();
        try
        {
            PackResult first = PackAdapter(Path.Combine(root, "first"));
            PackResult second = PackAdapter(Path.Combine(root, "second"));
            CollectionAssert.AreEqual(File.ReadAllBytes(first.Archive), File.ReadAllBytes(second.Archive), "The release archive is not byte deterministic.");
            AssertCanonicalZipMetadata(first.Archive);

            Dictionary<string, byte[]> entries = ReadArchive(first.Archive);
            foreach (string required in new[]
            {
                "extension.yml",
                "package-manifest.json",
                "README.md",
                "compatibility.json",
                "diagnostic-catalog.json",
                "release-files.json",
                "orbyss-program-kit-adapter-config.yml",
                "tools/program-kit-spec-kit-adapter.dll",
                "tools/program-kit-spec-kit-adapter.deps.json",
                "tools/program-kit-spec-kit-adapter.runtimeconfig.json",
            }) Assert.IsTrue(entries.ContainsKey(required), required);

            foreach (string generatedJson in new[]
            {
                "tools/program-kit-spec-kit-adapter.deps.json",
                "tools/program-kit-spec-kit-adapter.runtimeconfig.json",
            })
            {
                byte[] bytes = entries[generatedJson];
                Assert.IsFalse(bytes.AsSpan().StartsWith(Encoding.UTF8.Preamble), generatedJson);
                Assert.IsFalse(bytes.AsSpan().Contains((byte)'\r'), generatedJson);
                _ = CanonicalJson.Parse(bytes);
            }

            string[] expectedSchemas = Directory.EnumerateFiles(Path.Combine(TestRepository.Root, "src", "ProgramKit.SpecKitAdapter", "Schemas"), "*.schema.json")
                .Select(Path.GetFileName)
                .OrderBy(static value => value, StringComparer.Ordinal)
                .ToArray()!;
            string[] actualSchemas = entries.Keys.Where(static path => path.StartsWith("schemas/", StringComparison.Ordinal))
                .Select(Path.GetFileName)
                .OrderBy(static value => value, StringComparer.Ordinal)
                .ToArray()!;
            CollectionAssert.AreEqual(expectedSchemas, actualSchemas);

            JsonObject releaseFiles = CanonicalJson.Parse(entries["release-files.json"]).AsObject();
            Dictionary<string, string> declared = releaseFiles["files"]!.AsArray().Select(static node => node!.AsObject())
                .ToDictionary(static item => item["logicalPath"]!.GetValue<string>(), static item => item["digest"]!.GetValue<string>(), StringComparer.Ordinal);
            CollectionAssert.AreEquivalent(entries.Keys.Where(static path => path != "release-files.json").ToArray(), declared.Keys.ToArray());
            foreach ((string path, string digest) in declared) Assert.AreEqual(digest, Digest(entries[path]), path);

            JsonObject package = CanonicalJson.Parse(entries["package-manifest.json"]).AsObject();
            Assert.AreEqual("tools/program-kit-spec-kit-adapter.dll", package["entrypoint"]!.GetValue<string>());
            Assert.AreEqual("compatibility.json", package["publicContracts"]!["compatibility"]!.GetValue<string>());
            Assert.AreEqual("diagnostic-catalog.json", package["publicContracts"]!["diagnosticCatalog"]!.GetValue<string>());
            StringAssert.Contains(Encoding.UTF8.GetString(entries["extension.yml"]), "license: Proprietary", StringComparison.Ordinal);

            string[] forbiddenPaths = entries.Keys.Where(static path => path.EndsWith(".cs", StringComparison.OrdinalIgnoreCase)
                || path.EndsWith(".pdb", StringComparison.OrdinalIgnoreCase)
                || path.Contains("/eng/", StringComparison.OrdinalIgnoreCase)
                || path.Contains("/tests/", StringComparison.OrdinalIgnoreCase)
                || path.Contains(".agents/", StringComparison.OrdinalIgnoreCase))
                .ToArray();
            Assert.AreEqual(0, forbiddenPaths.Length, string.Join(Environment.NewLine, forbiddenPaths));
            AssertAssemblyReferences(entries["tools/program-kit-spec-kit-adapter.dll"]);
        }
        finally
        {
            TestRepository.DeleteWorkspace(root);
        }
    }

    [TestMethod]
    public void Tool_nupkg_contains_the_exact_executable_contract_runtime_and_no_adapter_or_self_hosting_files()
    {
        string root = TestRepository.CreateEmptyWorkspace();
        try
        {
            string output = Path.Combine(root, "tool");
            Directory.CreateDirectory(output);
            ProcessResult result = Run("dotnet", TestRepository.Root,
                "pack", Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "ProgramKit.Cli.csproj"),
                "--configuration", "Release", "--no-build", "--no-restore", "--output", output);
            Assert.AreEqual(0, result.ExitCode, result.Output + result.Error);
            string nupkg = Directory.EnumerateFiles(output, "Orbyss.ProgramKit.Cli.1.0.0-alpha.2.nupkg").Single();
            Dictionary<string, byte[]> entries = ReadArchive(nupkg);
            foreach (string suffix in new[]
            {
                "/program-kit.dll",
                "/program-kit.deps.json",
                "/program-kit.runtimeconfig.json",
                "/ProgramKit.Contracts.dll",
                "/ProgramKit.Kernel.dll",
                "/ProgramKit.Providers.DotNet.dll",
                "/ProgramKit.SessionIntegration.dll",
                "/ProgramKit.SessionIntegration.Providers.Codex.dll",
                "/DotnetToolSettings.xml",
                "/README.md",
            }) Assert.IsTrue(entries.Keys.Any(path => path.Equals(suffix.TrimStart('/'), StringComparison.OrdinalIgnoreCase)
                || path.EndsWith(suffix, StringComparison.OrdinalIgnoreCase)), suffix);

            Assert.IsFalse(entries.Keys.Any(static path => path.Contains("SpecKitAdapter", StringComparison.OrdinalIgnoreCase)));
            Assert.IsFalse(entries.Keys.Any(static path => path.EndsWith(".cs", StringComparison.OrdinalIgnoreCase)
                || path.Contains("/eng/", StringComparison.OrdinalIgnoreCase)
                || path.Contains("/tests/", StringComparison.OrdinalIgnoreCase)
                || path.Contains(".agents/", StringComparison.OrdinalIgnoreCase)));
            ZipEntry nuspecEntry = entries.Select(static item => new ZipEntry(item.Key, item.Value))
                .Single(static item => item.Path.EndsWith(".nuspec", StringComparison.OrdinalIgnoreCase));
            using MemoryStream nuspecStream = new(nuspecEntry.Bytes);
            XDocument nuspec = XDocument.Load(nuspecStream);
            Assert.AreEqual("Orbyss.ProgramKit.Cli", nuspec.Descendants().Single(static element => element.Name.LocalName == "id").Value);
            Assert.AreEqual("1.0.0-alpha.2", nuspec.Descendants().Single(static element => element.Name.LocalName == "version").Value);
            Assert.AreEqual("README.md", nuspec.Descendants().Single(static element => element.Name.LocalName == "readme").Value);
            Assert.IsTrue(nuspec.Descendants().Any(static element => element.Name.LocalName == "repository" && element.Attribute("type")?.Value == "git"));
            Assert.IsTrue(nuspec.Descendants().Where(static element => element.Name.LocalName == "dependency")
                .All(static dependency => !string.IsNullOrWhiteSpace(dependency.Attribute("id")?.Value)
                    && !string.IsNullOrWhiteSpace(dependency.Attribute("version")?.Value)));
        }
        finally
        {
            TestRepository.DeleteWorkspace(root);
        }
    }

    private static PackResult PackAdapter(string output)
    {
        string publishedTools = Path.Combine(TestRepository.Root, "src", "ProgramKit.SpecKitAdapter", "bin", "Release", "net10.0");
        ProcessResult result = Run("pwsh", TestRepository.Root, "-NoProfile", "-File", Path.Combine(TestRepository.Root, "eng", "Pack-SpecKitAdapter.ps1"), "-OutputRoot", output, "-PublishedToolsRoot", publishedTools);
        Assert.AreEqual(0, result.ExitCode, result.Output + result.Error);
        string json = result.Output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries).Last(static line => line.StartsWith('{'));
        JsonNode packed = JsonNode.Parse(json)!;
        return new PackResult(packed["ArchivePath"]!.GetValue<string>(), packed["StageRoot"]!.GetValue<string>());
    }

    private static Dictionary<string, byte[]> ReadArchive(string path)
    {
        using ZipArchive archive = ZipFile.OpenRead(path);
        return archive.Entries.Where(static entry => !string.IsNullOrEmpty(entry.Name))
            .ToDictionary(static entry => entry.FullName.Replace('\\', '/'), static entry =>
            {
                using Stream input = entry.Open();
                using MemoryStream bytes = new();
                input.CopyTo(bytes);
                return bytes.ToArray();
            }, StringComparer.Ordinal);
    }

    private static void AssertAssemblyReferences(byte[] assembly)
    {
        using PEReader reader = new(new MemoryStream(assembly));
        MetadataReader metadata = reader.GetMetadataReader();
        string[] references = metadata.AssemblyReferences.Select(handle => metadata.GetString(metadata.GetAssemblyReference(handle).Name)).ToArray();
        CollectionAssert.Contains(references, "ProgramKit.Contracts");
        foreach (string forbidden in new[] { "ProgramKit.Kernel", "ProgramKit.Providers", "ProgramKit.SessionIntegration", "SpecKit", "Microsoft.CodeAnalysis" })
            Assert.IsFalse(references.Any(name => name.Contains(forbidden, StringComparison.OrdinalIgnoreCase)), forbidden);
    }

    private static void AssertCanonicalZipMetadata(string path)
    {
        byte[] bytes = File.ReadAllBytes(path);
        int minimumEocdOffset = Math.Max(0, bytes.Length - 65_557);
        int eocdOffset = -1;
        for (int candidate = bytes.Length - 22; candidate >= minimumEocdOffset; candidate--)
        {
            if (BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(candidate, 4)) == 0x06054b50)
            {
                eocdOffset = candidate;
                break;
            }
        }

        Assert.IsTrue(eocdOffset >= 0, "ZIP end-of-central-directory record is missing.");
        int entryCount = BinaryPrimitives.ReadUInt16LittleEndian(bytes.AsSpan(eocdOffset + 10, 2));
        int entryOffset = checked((int)BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(eocdOffset + 16, 4)));
        for (int entryIndex = 0; entryIndex < entryCount; entryIndex++)
        {
            Assert.AreEqual(0x02014b50u, BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(entryOffset, 4)), $"entry {entryIndex}");
            Assert.AreEqual((byte)0, bytes[entryOffset + 5], $"entry {entryIndex} platform");
            Assert.AreEqual(0u, BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(entryOffset + 38, 4)), $"entry {entryIndex} attributes");
            int nameLength = BinaryPrimitives.ReadUInt16LittleEndian(bytes.AsSpan(entryOffset + 28, 2));
            int extraLength = BinaryPrimitives.ReadUInt16LittleEndian(bytes.AsSpan(entryOffset + 30, 2));
            int commentLength = BinaryPrimitives.ReadUInt16LittleEndian(bytes.AsSpan(entryOffset + 32, 2));
            entryOffset += 46 + nameLength + extraLength + commentLength;
        }
    }

    private static ProcessResult Run(string executable, string workingDirectory, params string[] arguments)
    {
        ProcessStartInfo start = new(executable) { WorkingDirectory = workingDirectory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true };
        foreach (string argument in arguments) start.ArgumentList.Add(argument);
        using Process process = Process.Start(start) ?? throw new InvalidOperationException($"Could not start {executable}.");
        Task<string> output = process.StandardOutput.ReadToEndAsync();
        Task<string> error = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(120_000))
        {
            process.Kill(entireProcessTree: true);
            process.WaitForExit();
            throw new TimeoutException($"{executable} package inspection exceeded two minutes.");
        }

        return new ProcessResult(process.ExitCode, output.GetAwaiter().GetResult(), error.GetAwaiter().GetResult());
    }

    private static string Digest(byte[] bytes) => "sha256:" + Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    private sealed record PackResult(string Archive, string Stage);
    private sealed record ZipEntry(string Path, byte[] Bytes);
}
