using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.SessionIntegration.Definitions;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class CanonicalSessionResourceContractTests
{
    [TestMethod]
    public void Canonical_definition_round_trips_complete_governed_content()
    {
        byte[] definitionBytes = Read(typeof(SessionIntegrationDefinitionLoader).Assembly, SessionIntegrationDefinitionLoader.DefinitionResourceSuffix);
        byte[] guidanceBytes = SessionIntegrationDefinitionLoader.ReadEmbeddedGuidance();
        SessionIntegrationDefinitionLoader loader = new();
        CanonicalSessionIntegrationDefinition first = loader.Load(definitionBytes, guidanceBytes);
        CanonicalSessionIntegrationDefinition second = loader.Load(CanonicalJson.Encode(CanonicalJson.Parse(definitionBytes)), guidanceBytes);

        Assert.AreEqual(first.Identity, second.Identity);
        Assert.AreEqual(first.Fingerprint, second.Fingerprint);
        CollectionAssert.AreEqual(first.OperationContracts.ToArray(), second.OperationContracts.ToArray());
        CollectionAssert.AreEqual(first.SessionLifecycleContracts.ToArray(), second.SessionLifecycleContracts.ToArray());
        CollectionAssert.AreEqual(first.DiagnosticCatalogs.ToArray(), second.DiagnosticCatalogs.ToArray());
        Assert.AreEqual(first.Identity.Digest, first.Fingerprint);
        Assert.AreNotEqual("sha256:" + new string('0', 64), first.Fingerprint);
        CollectionAssert.AreEquivalent(new[] { "construct", "session-install", "session-remove" }, first.AuthorityRules.HumanApprovalRequiredFor.ToArray());
        CollectionAssert.AreEquivalent(new[] { "explain", "evaluate", "session-explain", "session-verify" }, first.EffectClasses.ReadOnly.ToArray());
        Assert.AreEqual("json-stdout", first.ResultRules.AuthoritativeChannel);
        Assert.IsTrue(first.ResultRules.DiagnosticIdentityRequired);
        Assert.AreEqual("workspace-root", first.ProjectionRequirements.WorkingDirectory);
        Assert.AreEqual(2, first.DiagnosticCatalogs.Count);
        Assert.AreEqual(Digests.Sha256(guidanceBytes), first.GuidanceArtifact.Digest);
    }

    [TestMethod]
    public void Canonical_definition_rejects_content_or_guidance_drift()
    {
        byte[] definitionBytes = Read(typeof(SessionIntegrationDefinitionLoader).Assembly, SessionIntegrationDefinitionLoader.DefinitionResourceSuffix);
        byte[] guidanceBytes = SessionIntegrationDefinitionLoader.ReadEmbeddedGuidance();
        JsonObject drifted = CanonicalJson.Parse(definitionBytes).AsObject();
        drifted["projectionRequirements"]!["workingDirectory"] = "different-root";

        SessionIntegrationDefinitionLoader loader = new();
        Assert.ThrowsExactly<InvalidDataException>(() => loader.Load(CanonicalJson.Encode(drifted), guidanceBytes));
        Assert.ThrowsExactly<InvalidDataException>(() => loader.Load(definitionBytes, guidanceBytes.Concat(new byte[] { 0x20 }).ToArray()));
    }

    [TestMethod]
    public void Embedded_codex_manifest_is_the_single_runtime_source_and_binds_the_definition()
    {
        CodexSessionProviderManifestLoader loader = new();
        SessionProviderManifest loaded = loader.LoadEmbedded();
        SessionProviderManifest runtime = new CodexSessionProviderAdapter().Manifest;

        Assert.AreEqual(loaded.ProviderIdentity, runtime.ProviderIdentity);
        Assert.AreEqual(loaded.AdapterIdentity, runtime.AdapterIdentity);
        Assert.AreEqual(loaded.DefinitionBinding, runtime.DefinitionBinding);
        Assert.AreEqual(loaded.ProviderSurface.ProviderName, runtime.ProviderSurface.ProviderName);
        CollectionAssert.AreEqual(loaded.ProviderSurface.TestedVersions.ToArray(), runtime.ProviderSurface.TestedVersions.ToArray());
        CollectionAssert.AreEqual(loaded.ProjectionDescriptors.ToArray(), runtime.ProjectionDescriptors.ToArray());
        CollectionAssert.AreEqual(loaded.RequiredCliOperations.ToArray(), runtime.RequiredCliOperations.ToArray());
        Assert.AreEqual(CanonicalSessionGuidance.Definition.Identity, runtime.DefinitionBinding);
        Assert.AreEqual("program-kit.canonical-json/v1", runtime.CanonicalProfile);
        Assert.AreEqual("repository-skill", runtime.ProviderSurface.SurfaceName);
        Assert.IsTrue(runtime.ProviderSurface.TestedVersions.Count > 0);
        Assert.AreNotEqual("sha256:" + new string('0', 64), runtime.ProviderIdentity.Digest);
        Assert.AreEqual(runtime.ProviderIdentity.Digest, runtime.AdapterIdentity.Digest);
    }

    [TestMethod]
    public void Codex_manifest_rejects_placeholder_and_divergent_runtime_identities()
    {
        byte[] manifestBytes = Read(typeof(CodexSessionProviderManifestLoader).Assembly, ".Resources.codex-provider-manifest.json");
        JsonObject placeholder = CanonicalJson.Parse(manifestBytes).AsObject();
        placeholder["providerIdentity"]!["digest"] = "sha256:" + new string('0', 64);
        JsonObject divergent = CanonicalJson.Parse(manifestBytes).AsObject();
        divergent["definitionBinding"]!["digest"] = "sha256:" + new string('1', 64);
        CodexSessionProviderManifestLoader loader = new();

        Assert.ThrowsExactly<InvalidDataException>(() => loader.Load(CanonicalJson.Encode(placeholder)));
        Assert.ThrowsExactly<InvalidDataException>(() => loader.Load(CanonicalJson.Encode(divergent)));
    }

    private static byte[] Read(Assembly assembly, string suffix)
    {
        string name = assembly.GetManifestResourceNames().Single(item => item.EndsWith(suffix, StringComparison.Ordinal));
        using Stream stream = assembly.GetManifestResourceStream(name) ?? throw new InvalidOperationException(name);
        using MemoryStream buffer = new();
        stream.CopyTo(buffer);
        return buffer.ToArray();
    }
}
