using System;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class AdapterPublicContractTests
{
    private static readonly string[] NewSchemaIds =
    {
        ContractSchemaResources.DistributionBindingId,
        ContractSchemaResources.WorkspaceInitializationRequestId,
        ContractSchemaResources.WorkspaceManifestId,
        ContractSchemaResources.CatalogRequestId,
        ContractSchemaResources.DistributionCatalogId,
        ContractSchemaResources.WorkspaceRestoreRequestId,
        ContractSchemaResources.WorkspaceLockId,
        ContractSchemaResources.PreparationRequestId,
        ContractSchemaResources.PreparationProposalId,
        ContractSchemaResources.AuthorityDecisionRecordId,
        ContractSchemaResources.AuthorityRecordRequestId,
        ContractSchemaResources.OperationResultId,
    };

    [TestMethod]
    public void New_public_schemas_are_closed_reachable_and_exactly_versioned()
    {
        SchemaRegistry registry = new();
        foreach (string id in NewSchemaIds)
        {
            JsonObject schema = registry.Get(id).AsObject();
            JsonObject closedDocument = id == ContractSchemaResources.OperationResultId
                ? schema["$defs"]!["operationResult"]!.AsObject()
                : schema;
            Assert.AreEqual(false, closedDocument["additionalProperties"]!.GetValue<bool>(), id);
            Assert.IsTrue(closedDocument["required"]!.AsArray().Count > 0, id);
            Assert.IsNotNull(registry.GetCompiled(id), id);
        }
    }

    [TestMethod]
    public void New_public_schemas_reject_missing_bindings_and_open_top_level_properties()
    {
        StructuralSchemaValidator validator = new(new SchemaRegistry());
        foreach (string id in NewSchemaIds)
        {
            JsonObject empty = new();
            Assert.IsTrue(validator.Validate(id, empty).Count > 0, id);

            JsonObject withUnknown = new() { ["unexpected"] = true };
            Assert.IsTrue(validator.Validate(id, withUnknown).Count > 0, id);
        }
    }

    [TestMethod]
    public void One_current_result_contract_contains_every_public_command_without_a_parallel_legacy_surface()
    {
        string[] resultTypes = typeof(OperationResult).Assembly.GetExportedTypes()
            .Where(static type => string.Equals(type.Namespace, typeof(OperationResult).Namespace, StringComparison.Ordinal)
                && type.Name.StartsWith("OperationResult", StringComparison.Ordinal))
            .Select(static type => type.Name)
            .OrderBy(static name => name, StringComparer.Ordinal)
            .ToArray();
        CollectionAssert.AreEqual(new[] { "OperationResult" }, resultTypes);

        string[] commandTypes = typeof(PublicCommand).Assembly.GetExportedTypes()
            .Where(static type => string.Equals(type.Namespace, typeof(PublicCommand).Namespace, StringComparison.Ordinal)
                && type.Name.StartsWith("PublicCommand", StringComparison.Ordinal))
            .Select(static type => type.Name)
            .OrderBy(static name => name, StringComparer.Ordinal)
            .ToArray();
        CollectionAssert.AreEqual(new[] { "PublicCommand" }, commandTypes);

        string[] commands = Enum.GetNames<PublicCommand>();
        CollectionAssert.AreEqual(
            new[] { "Explain", "Construct", "Evaluate", "SessionExplain", "SessionInstall", "SessionVerify", "SessionRemove", "Init", "CatalogList", "Restore", "Prepare", "AuthorityRecord", "Help", "Version" },
            commands);

        string currentSchema = ContractSchemaResources.ReadById(ContractSchemaResources.OperationResultId);
        Assert.IsTrue(currentSchema.Contains("catalog-list", StringComparison.Ordinal));
        Assert.ThrowsExactly<InvalidOperationException>(() => ContractSchemaResources.ReadById("https://schemas.program-kit.dev/v1/operation-result.schema.json"));
    }
}
