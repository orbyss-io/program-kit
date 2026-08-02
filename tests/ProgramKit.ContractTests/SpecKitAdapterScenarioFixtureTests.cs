using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterScenarioFixtureTests
{
    [TestMethod]
    public void Two_reviewed_factory_fixtures_are_valid_canonical_and_semantically_distinct()
    {
        ScenarioProjection reference = Project(SpecKitAdapterFixture.ReferenceStatus);
        ScenarioProjection inventory = Project(SpecKitAdapterFixture.InventoryHealth);

        Assert.AreNotEqual(reference.FeatureKey, inventory.FeatureKey);
        Assert.AreNotEqual(reference.ComponentName, inventory.ComponentName);
        Assert.AreNotEqual(reference.Namespace, inventory.Namespace);
        Assert.AreNotEqual(reference.ContractName, inventory.ContractName);
        Assert.AreNotEqual(reference.ApplicationName, inventory.ApplicationName);
        Assert.AreNotEqual(reference.Route, inventory.Route);
        Assert.AreNotEqual(reference.ImplementationDigest, inventory.ImplementationDigest);
        Assert.AreNotEqual(reference.DefinitionDigest, inventory.DefinitionDigest);
        Assert.AreNotEqual(reference.BundleDigest, inventory.BundleDigest);
        Assert.AreNotEqual(reference.PreparationDigest, inventory.PreparationDigest);
        Assert.AreNotEqual(reference.ExplainDigest, inventory.ExplainDigest);
        StringAssert.Contains(inventory.Implementation, "new(\"degraded\", 7)", StringComparison.Ordinal);
        StringAssert.Contains(inventory.Implementation, "AddScoped<IInventoryProbe, InventoryProbe>", StringComparison.Ordinal);
    }

    private static ScenarioProjection Project(SpecKitAdapterScenario scenario)
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace(scenario);
        try
        {
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(
                workspace,
                SpecKitAdapterFixture.AdapterRequest(scenario, "validate"),
                requireReviewedHandoff: true);
            var handoff = context.Handoff ?? throw new InvalidOperationException("The reviewed fixture handoff was not loaded.");
            TranslationResult translation = new DotNetHandoffTranslator().Translate(handoff, context.WorkspaceLock);
            JsonObject definition = translation.Documents.Single(item => item.Key.EndsWith("/dotnet-component-api.json", StringComparison.Ordinal)).Value;
            JsonObject bundle = translation.Documents.Single(item => item.Key.EndsWith("/software-bundle.json", StringComparison.Ordinal)).Value;
            JsonObject preparation = translation.Documents.Single(item => item.Key.EndsWith("/prepare.json", StringComparison.Ordinal)).Value;
            JsonObject explain = translation.Documents.Single(item => item.Key.EndsWith("/explain.json", StringComparison.Ordinal)).Value;
            ContractAssertions.AssertValid("https://schemas.program-kit.dev/v1/software-definition-bundle.schema.json", bundle);
            ContractAssertions.AssertValid(ContractSchemaResources.PreparationRequestId, preparation);
            ContractAssertions.AssertValid(ContractAssertions.FactoryRequest, explain);

            JsonObject component = definition["component"]!.AsObject();
            JsonObject application = definition["application"]!.AsObject();
            string implementationPath = handoff.Document["implementation"]![0]!["logicalPath"]!.GetValue<string>();
            return new ScenarioProjection(
                handoff.Document["feature"]!["key"]!.GetValue<string>(),
                component["name"]!.GetValue<string>(),
                component["namespace"]!.GetValue<string>(),
                component["contractName"]!.GetValue<string>(),
                application["name"]!.GetValue<string>(),
                application["route"]!.GetValue<string>(),
                handoff.Document["implementation"]![0]!["digest"]!.GetValue<string>(),
                CanonicalDocument.Digest(definition),
                CanonicalDocument.Digest(bundle),
                CanonicalDocument.Digest(preparation),
                CanonicalDocument.Digest(explain),
                File.ReadAllText(Path.Combine(workspace, implementationPath.Replace('/', Path.DirectorySeparatorChar))));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private sealed record ScenarioProjection(
        string FeatureKey,
        string ComponentName,
        string Namespace,
        string ContractName,
        string ApplicationName,
        string Route,
        string ImplementationDigest,
        string DefinitionDigest,
        string BundleDigest,
        string PreparationDigest,
        string ExplainDigest,
        string Implementation);
}
