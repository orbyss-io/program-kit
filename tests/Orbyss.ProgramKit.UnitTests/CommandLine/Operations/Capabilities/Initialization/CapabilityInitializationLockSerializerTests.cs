using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Capabilities.Initialization;

[TestClass]
public sealed class CapabilityInitializationLockSerializerTests
{
    private const string Digest =
        "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    [TestMethod]
    public void CurrentMultiProviderLockRoundTripsInExactStableOrder()
    {
        CapabilityInitializationLockSerializer sut = new();
        CapabilityInitializationLock value = new(
            "2.0.0",
            [
                Provider("claude", ".claude/skills/design-software/SKILL.md"),
                Provider("codex", ".agents/skills/design-software/SKILL.md"),
            ]);

        var first = sut.Write(value);
        var second = sut.Write(sut.Read(first));

        Assert.AreSequenceEqual(first, second);
        var roundTrip = sut.Read(first);
        Assert.AreEqual("2.0.0", roundTrip.LockVersion);
        Assert.AreSequenceEqual(
            ["claude", "codex"],
            roundTrip.Providers.Select(static provider => provider.Provider));
        var json = Encoding.UTF8.GetString(first);
        Assert.Contains("\"lockVersion\":\"2.0.0\"", json);
        Assert.Contains("\"providers\":[", json);
        Assert.DoesNotContain("\"provider\":\"cursor\"", json);
    }

    [TestMethod]
    public void ExactLegacyWireShapeReadsAsOneMigratableProviderBinding()
    {
        CapabilityInitializationLockSerializer sut = new();
        var legacy = Encoding.UTF8.GetBytes(
            $$"""
            {"lockVersion":"1.0.0","bundleVersion":"3.0.0","provider":"codex","programKitRoot":"program-kit","manifestSha256":"{{Digest}}","capabilities":[{"capabilityId":"design-software","canonicalPath":"program-kit/.agent-capabilities/capabilities/design-software/CAPABILITY.md","canonicalSha256":"{{Digest}}","adapterTemplateSha256":"{{Digest}}","outputPath":".codex/skills/design-software/SKILL.md","outputSha256":"{{Digest}}"}]}
            """);

        var result = sut.Read(legacy);

        Assert.AreEqual("1.0.0", result.LockVersion);
        Assert.HasCount(1, result.Providers);
        Assert.AreEqual("codex", result.Providers[0].Provider);
        Assert.AreEqual(
            ".codex/skills/design-software/SKILL.md",
            result.Providers[0].Capabilities[0].OutputPath);
    }

    [TestMethod]
    public void UnknownVersionMembersAndDuplicatePropertiesFailClosed()
    {
        CapabilityInitializationLockSerializer sut = new();
        var unknownVersion = Encoding.UTF8.GetBytes(
            """{"lockVersion":"9.0.0","providers":[]}""");
        var unknownMember = Encoding.UTF8.GetBytes(
            """{"lockVersion":"2.0.0","providers":[],"unexpected":true}""");
        var duplicateVersion = Encoding.UTF8.GetBytes(
            """{"lockVersion":"1.0.0","lockVersion":"2.0.0","providers":[]}""");

        Assert.ThrowsExactly<JsonException>(() => sut.Read(unknownVersion));
        Assert.ThrowsExactly<JsonException>(() => sut.Read(unknownMember));
        Assert.ThrowsExactly<JsonException>(() => sut.Read(duplicateVersion));
    }

    private static CapabilityProviderInitializationLock Provider(
        string provider,
        string outputPath) =>
        new(
            provider,
            "4.0.0",
            "program-kit",
            Digest,
            [
                new CapabilityInitializationLockEntry(
                    "design-software",
                    "program-kit/.agent-capabilities/capabilities/design-software/CAPABILITY.md",
                    Digest,
                    Digest,
                    outputPath,
                    Digest),
            ]);
}
