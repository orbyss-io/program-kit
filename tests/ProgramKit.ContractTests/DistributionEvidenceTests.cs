using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Providers.DotNet.Manifests;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Diagnostics;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class DistributionEvidenceTests
{
    [TestMethod]
    public void Distribution_evidence_is_canonical_exact_and_matches_runtime_catalog_and_support()
    {
        string generator = File.ReadAllText(Path.Combine(TestRepository.Root, "eng", "Generate-DistributionEvidence.ps1"));
        StringAssert.Contains(generator, "Pack-SpecKitAdapter.ps1') -OutputRoot $adapterPackageRoot");
        Assert.IsFalse(generator.Contains("-PublishedToolsRoot", StringComparison.Ordinal));

        string evidenceRoot = Path.Combine(TestRepository.Root, "artifacts", "evidence");
        JsonObject manifest = Read(Path.Combine(evidenceRoot, "distribution-manifest.json"));
        foreach (JsonObject artifact in manifest["artifacts"]!.AsArray().Select(static node => node!.AsObject()))
        {
            string path = Path.Combine(TestRepository.Root, artifact["logicalPath"]!.GetValue<string>().Replace('/', Path.DirectorySeparatorChar));
            Assert.IsTrue(File.Exists(path), path);
            Assert.AreEqual(artifact["digest"]!.GetValue<string>(), Digest(path));
            CollectionAssert.AreEqual(File.ReadAllBytes(path), CanonicalJson.Encode(CanonicalJson.Parse(File.ReadAllBytes(path))));
        }

        JsonObject support = Read(Path.Combine(evidenceRoot, "provider-support.json"));
        var provider = DotNetProviderManifest.Create();
        Assert.AreEqual(provider.Identity.Digest, support["provider"]!["digest"]!.GetValue<string>());
        CollectionAssert.AreEqual(provider.Profiles.OrderBy(static item => item, StringComparer.Ordinal).ToArray(), Values(support, "profiles"));
        CollectionAssert.AreEqual(provider.InputKinds.OrderBy(static item => item, StringComparer.Ordinal).ToArray(), Values(support, "inputKinds"));
        CollectionAssert.AreEqual(provider.OutputKinds.OrderBy(static item => item, StringComparer.Ordinal).ToArray(), Values(support, "outputKinds"));

        JsonObject kernelCatalog = Read(Path.Combine(evidenceRoot, "kernel-diagnostic-catalog.json"));
        JsonObject providerCatalog = Read(Path.Combine(evidenceRoot, "dotnet-diagnostic-catalog.json"));
        JsonObject sessionCatalog = Read(Path.Combine(evidenceRoot, "session-diagnostic-catalog.json"));
        JsonObject codexCatalog = Read(Path.Combine(evidenceRoot, "codex-diagnostic-catalog.json"));
        Assert.AreEqual(DiagnosticCatalogArtifacts.KernelIdentity.Digest, Digest(Path.Combine(evidenceRoot, "kernel-diagnostic-catalog.json")));
        Assert.AreEqual(DiagnosticCatalogArtifacts.DotNetIdentity.Digest, Digest(Path.Combine(evidenceRoot, "dotnet-diagnostic-catalog.json")));
        Assert.AreEqual(SessionDiagnosticCatalog.Identity.Digest, Digest(Path.Combine(evidenceRoot, "session-diagnostic-catalog.json")));
        Assert.AreEqual(CodexDiagnosticCatalog.Identity.Digest, Digest(Path.Combine(evidenceRoot, "codex-diagnostic-catalog.json")));
        Assert.AreEqual(provider.DiagnosticCatalog.Identity.Digest, provider.DiagnosticCatalog.Digest);
        Assert.AreEqual(provider.DiagnosticCatalog.Digest, Digest(Path.Combine(TestRepository.Root, provider.DiagnosticCatalog.LogicalPath.Replace('/', Path.DirectorySeparatorChar))));
        Assert.IsTrue(provider.ConformanceEvidence.Count > 0);
        Assert.IsTrue(provider.ConformanceEvidence.All(item => item.Artifact.Identity.Digest == item.Artifact.Digest));
        Assert.IsTrue(provider.ConformanceEvidence.All(item => item.Artifact.Digest == Digest(Path.Combine(TestRepository.Root, item.Artifact.LogicalPath.Replace('/', Path.DirectorySeparatorChar)))));
        Assert.AreEqual(provider.DiagnosticCatalog.Digest, manifest["diagnosticCatalog"]!["digest"]!.GetValue<string>());
        Assert.AreEqual(provider.ConformanceEvidence[0].Artifact.Digest, manifest["conformanceEvidence"]![0]!["artifact"]!["digest"]!.GetValue<string>());
        ContractAssertions.AssertValid(ContractAssertions.OperationResult, kernelCatalog);
        ContractAssertions.AssertValid(ContractAssertions.OperationResult, providerCatalog);
        ContractAssertions.AssertValid(ContractAssertions.OperationResult, sessionCatalog);
        ContractAssertions.AssertValid(ContractAssertions.OperationResult, codexCatalog);
        string[] expectedIds = DiagnosticCatalog.Entries.Keys.OrderBy(static item => item, StringComparer.Ordinal).ToArray();
        string[] actualIds = kernelCatalog["entries"]!.AsArray()
            .Concat(providerCatalog["entries"]!.AsArray())
            .Select(static item => item!["id"]!.GetValue<string>())
            .OrderBy(static item => item, StringComparer.Ordinal)
            .ToArray();
        CollectionAssert.AreEqual(expectedIds, actualIds);
        Assert.IsTrue(kernelCatalog["entries"]!.AsArray().All(static item => item!["primaryDisposition"] is not null));
        Assert.IsTrue(providerCatalog["entries"]!.AsArray().All(static item => item!["primaryDisposition"] is not null));
        CollectionAssert.AreEqual(SessionDiagnosticCatalog.Entries.Keys.ToArray(), sessionCatalog["entries"]!.AsArray().Select(static item => item!["id"]!.GetValue<string>()).ToArray());
        CollectionAssert.AreEqual(CodexDiagnosticCatalog.Entries.Keys.ToArray(), codexCatalog["entries"]!.AsArray().Select(static item => item!["id"]!.GetValue<string>()).ToArray());

        JsonObject sbom = Read(Path.Combine(evidenceRoot, "dependency-sbom.cdx.json"));
        Assert.IsTrue(sbom["components"]!.AsArray().Count > 0);
        Assert.IsTrue(sbom["components"]!.AsArray().All(static component => !string.IsNullOrWhiteSpace(component!["version"]!.GetValue<string>())));
        JsonObject provenance = Read(Path.Combine(evidenceRoot, "source-package-provenance.json"));
        Assert.AreEqual(CanonicalJson.Digest(provenance["sourceArtifacts"]!), provenance["sourceClosureDigest"]!.GetValue<string>());
        Assert.AreEqual(CanonicalJson.Digest(provenance["packageArtifacts"]!), provenance["packageClosureDigest"]!.GetValue<string>());
        foreach (JsonObject source in provenance["sourceArtifacts"]!.AsArray().Select(static node => node!.AsObject()))
        {
            string logicalPath = source["logicalPath"]!.GetValue<string>();
            string path = Path.Combine(TestRepository.Root, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            byte[] bytes = File.ReadAllBytes(path);
            Assert.IsFalse(bytes.AsSpan().StartsWith(Encoding.UTF8.Preamble), logicalPath);
            Assert.IsFalse(bytes.AsSpan().Contains((byte)'\r'), logicalPath);
            _ = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false, throwOnInvalidBytes: true).GetString(bytes);
            Assert.AreEqual(source["digest"]!.GetValue<string>(), Digest(path), logicalPath);
        }

        JsonObject adapter = Read(Path.Combine(evidenceRoot, "spec-kit-adapter-distribution-evidence.json"));
        JsonObject release = adapter["release"]!.AsObject();
        JsonObject bindings = adapter["claimInvalidationBindings"]!.AsObject();
        Assert.AreEqual("orbyss-program-kit-adapter@0.1.0", release["identity"]!.GetValue<string>());
        Assert.AreEqual(AdapterCompatibility.Load().Digest, adapter["compatibility"]!["digest"]!.GetValue<string>());
        Assert.AreEqual(AdapterDiagnosticCatalog.Digest, adapter["diagnosticCatalog"]!["digest"]!.GetValue<string>());
        Assert.AreEqual(CanonicalJson.Digest(release), bindings["release"]!.GetValue<string>());
        Assert.AreEqual(CanonicalJson.Digest(adapter["publicSchemas"]!), bindings["publicSchemas"]!.GetValue<string>());
        Assert.AreEqual(AdapterDiagnosticCatalog.Digest, bindings["diagnosticCatalog"]!.GetValue<string>());
        Assert.AreEqual(Digest(Path.Combine(evidenceRoot, "provider-support.json")), bindings["providerSupport"]!.GetValue<string>());
        string packageRoot = Path.Combine(TestRepository.Root, "artifacts", "work", "evidence-adapter-package");
        string packagedTools = Path.Combine(packageRoot, "orbyss-program-kit-adapter-0.1.0", "tools");
        string archive = Path.Combine(packageRoot, "orbyss-program-kit-adapter-0.1.0.zip");
        string releaseFiles = Path.Combine(packageRoot, "orbyss-program-kit-adapter-0.1.0", "release-files.json");
        AssertStableReleaseAssembly(Path.Combine(packagedTools, "program-kit-spec-kit-adapter.dll"), "0.1.0", forbidWin32Manifest: true);
        AssertStableReleaseAssembly(Path.Combine(packagedTools, "ProgramKit.Contracts.dll"), "1.0.0", forbidWin32Manifest: false);
        Assert.AreEqual(release["archiveDigest"]!.GetValue<string>(), Digest(archive));
        Assert.AreEqual(release["releaseFilesDigest"]!.GetValue<string>(), Digest(releaseFiles));
        JsonObject releaseFilesDocument = Read(releaseFiles);
        Assert.AreEqual(release["releaseClosureDigest"]!.GetValue<string>(), CanonicalJson.Digest(releaseFilesDocument["files"]!));
        Dictionary<string, string> schemaDigests = adapter["publicSchemas"]!.AsArray().Select(static node => node!.AsObject())
            .ToDictionary(static schema => schema["identity"]!.GetValue<string>(), static schema => schema["digest"]!.GetValue<string>(), StringComparer.Ordinal);
        foreach (string schemaText in AdapterSchemaResources.ReadAll().Values)
        {
            JsonObject schema = JsonNode.Parse(schemaText)!.AsObject();
            Assert.AreEqual(CanonicalJson.Digest(schema), schemaDigests[schema["$id"]!.GetValue<string>()]);
        }

        JsonObject staleRelease = (JsonObject)release.DeepClone();
        staleRelease["archiveDigest"] = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
        Assert.AreNotEqual(bindings["release"]!.GetValue<string>(), CanonicalJson.Digest(staleRelease));
    }

    private static JsonObject Read(string path) => CanonicalJson.Parse(File.ReadAllBytes(path)).AsObject();
    private static void AssertStableReleaseAssembly(string path, string productVersion, bool forbidWin32Manifest)
    {
        using FileStream stream = File.OpenRead(path);
        using PEReader reader = new(stream);
        Assert.IsFalse(reader.ReadDebugDirectory().Any(static entry => entry.Type == DebugDirectoryEntryType.CodeView), path);
        Assert.AreEqual(productVersion, FileVersionInfo.GetVersionInfo(path).ProductVersion, path);
        if (forbidWin32Manifest)
            Assert.AreEqual(-1, File.ReadAllBytes(path).AsSpan().IndexOf("urn:schemas-microsoft-com:asm.v1"u8), path);
    }

    private static string Digest(string path) => $"sha256:{Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant()}";
    private static string[] Values(JsonObject document, string name) => document[name]!.AsArray().Select(static item => item!.GetValue<string>()).ToArray();
}
