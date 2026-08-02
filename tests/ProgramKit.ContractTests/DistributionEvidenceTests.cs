using System;
using System.IO;
using System.Linq;
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

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class DistributionEvidenceTests
{
    [TestMethod]
    public void Distribution_evidence_is_canonical_exact_and_matches_runtime_catalog_and_support()
    {
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
    }

    private static JsonObject Read(string path) => CanonicalJson.Parse(File.ReadAllBytes(path)).AsObject();
    private static string Digest(string path) => $"sha256:{Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant()}";
    private static string[] Values(JsonObject document, string name) => document[name]!.AsArray().Select(static item => item!.GetValue<string>()).ToArray();
}
