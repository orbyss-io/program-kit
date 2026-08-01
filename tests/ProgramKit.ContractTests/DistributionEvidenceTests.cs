using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Providers.DotNet.Manifests;

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

        JsonObject catalog = Read(Path.Combine(evidenceRoot, "diagnostic-catalog.json"));
        string[] expectedIds = DiagnosticCatalog.Entries.Keys.OrderBy(static item => item, StringComparer.Ordinal).ToArray();
        string[] actualIds = catalog["entries"]!.AsArray().Select(static item => item!["id"]!.GetValue<string>()).ToArray();
        CollectionAssert.AreEqual(expectedIds, actualIds);

        JsonObject sbom = Read(Path.Combine(evidenceRoot, "dependency-sbom.cdx.json"));
        Assert.IsTrue(sbom["components"]!.AsArray().Count > 0);
        Assert.IsTrue(sbom["components"]!.AsArray().All(static component => !string.IsNullOrWhiteSpace(component!["version"]!.GetValue<string>())));
        JsonObject provenance = Read(Path.Combine(evidenceRoot, "source-package-provenance.json"));
        Assert.AreEqual(CanonicalJson.Digest(provenance["sourceArtifacts"]!), provenance["sourceClosureDigest"]!.GetValue<string>());
        Assert.AreEqual(CanonicalJson.Digest(provenance["packageArtifacts"]!), provenance["packageClosureDigest"]!.GetValue<string>());
    }

    private static JsonObject Read(string path) => CanonicalJson.Parse(File.ReadAllBytes(path)).AsObject();
    private static string Digest(string path) => $"sha256:{Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant()}";
    private static string[] Values(JsonObject document, string name) => document[name]!.AsArray().Select(static item => item!.GetValue<string>()).ToArray();
}
