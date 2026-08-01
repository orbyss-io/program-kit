using System.Linq;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode;
using Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class ClaudeConformanceProfileContractTests
{
    [TestMethod]
    public void Profile_binds_exact_provider_adapter_definition_catalog_schema_and_neutral_operations()
    {
        ClaudeSessionProviderAdapter adapter = new();
        ClaudeConformanceProfile profile = ClaudeConformanceProfiles.ProjectSkillV1(adapter.Manifest);
        Assert.AreEqual(adapter.Manifest.ProviderIdentity, profile.Provider);
        Assert.AreEqual(adapter.Manifest.AdapterIdentity, profile.Adapter);
        Assert.AreEqual(adapter.Manifest.DefinitionBinding, profile.Definition);
        Assert.AreEqual(adapter.Manifest.DiagnosticCatalog, profile.DiagnosticCatalog);
        Assert.AreEqual("https://schemas.program-kit.dev/v1/claude-code-machine-review.schema.json", profile.ReviewSchema);
        CollectionAssert.AreEqual(adapter.Manifest.RequiredCliOperations.ToArray(), profile.RequiredOperations.ToArray());
        Assert.AreEqual("not-evaluated", profile.LiveEvidenceStatus);
    }
}
