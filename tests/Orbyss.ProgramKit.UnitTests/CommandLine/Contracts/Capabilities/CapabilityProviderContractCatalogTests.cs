using Orbyss.ProgramKit.CommandLine.Contracts.Capabilities;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Contracts.Capabilities;

[TestClass]
public sealed class CapabilityProviderContractCatalogTests
{
    [TestMethod]
    public void CatalogContainsOnlyExactReviewedProjectSkillContracts()
    {
        Assert.AreSequenceEqual(
            ["claude", "codex"],
            CapabilityProviderContractCatalog.All.Select(
                static contract => contract.ProviderId));
        Assert.AreEqual(
            ".claude/skills/",
            CapabilityProviderContractCatalog.All[0].ProjectSkillRoot);
        Assert.IsNull(
            CapabilityProviderContractCatalog.All[0].LegacyProjectSkillRoot);
        Assert.AreEqual(
            ".agents/skills/",
            CapabilityProviderContractCatalog.All[1].ProjectSkillRoot);
        Assert.AreEqual(
            ".codex/skills/",
            CapabilityProviderContractCatalog.All[1].LegacyProjectSkillRoot);
    }

    [TestMethod]
    public void LookupIsExactAndRejectsUnreviewedProviders()
    {
        Assert.IsTrue(
            CapabilityProviderContractCatalog.TryGet("codex", out var codex));
        Assert.AreEqual(".agents/skills/", codex.ProjectSkillRoot);
        Assert.IsFalse(
            CapabilityProviderContractCatalog.TryGet("Codex", out _));
        Assert.IsFalse(
            CapabilityProviderContractCatalog.TryGet("cursor", out _));
        Assert.IsFalse(
            CapabilityProviderContractCatalog.TryGet(null, out _));
    }
}
