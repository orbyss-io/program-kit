using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterTranslationContractTests
{
    [TestMethod]
    public void Reviewed_handoff_translates_five_times_and_under_object_permutation_to_identical_bytes()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true);
            DotNetHandoffTranslator translator = new();
            TranslationResult expected = translator.Translate(context.Handoff!, context.WorkspaceLock);
            for (int repeat = 0; repeat < 5; repeat++) AssertBytesEqual(expected.Bytes, translator.Translate(context.Handoff!, context.WorkspaceLock).Bytes);

            JsonObject permutedDocument = ReverseObjects(context.Handoff!.Document).AsObject();
            BoundHandoff permuted = new HandoffBinder().Bind(permutedDocument, requireComplete: true);
            Assert.AreEqual(context.Handoff.Digest, permuted.Digest);
            AssertBytesEqual(expected.Bytes, translator.Translate(permuted, ReverseObjects(context.WorkspaceLock).AsObject()).Bytes);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Translation_is_complete_schema_valid_selection_bound_and_contains_no_authority_grant()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true);
            TranslationResult translation = new DotNetHandoffTranslator().Translate(context.Handoff!, context.WorkspaceLock);
            JsonObject bundle = translation.Documents.Single(item => item.Key.EndsWith("/software-bundle.json", StringComparison.Ordinal)).Value;
            JsonObject preparation = translation.Documents.Single(item => item.Key.EndsWith("/prepare.json", StringComparison.Ordinal)).Value;
            JsonObject explanation = translation.Documents.Single(item => item.Key.EndsWith("/explain.json", StringComparison.Ordinal)).Value;
            ContractAssertions.AssertValid("https://schemas.program-kit.dev/v1/software-definition-bundle.schema.json", bundle);
            ContractAssertions.AssertValid(ContractSchemaResources.PreparationRequestId, preparation);
            ContractAssertions.AssertValid(ContractAssertions.FactoryRequest, explanation);
            Assert.AreEqual(IntakePipeline.DocumentIdentityDigest(bundle), bundle["identity"]!["digest"]!.GetValue<string>());
            Assert.AreEqual(4, preparation["selections"]!.AsArray().Count);
            Assert.AreEqual(4, preparation["selections"]!.AsArray().Select(static item => item!["role"]!.GetValue<string>()).Distinct(StringComparer.Ordinal).Count());
            Assert.AreEqual("candidate-only", preparation["desiredEffect"]!.GetValue<string>());
            Assert.IsFalse(ContainsProperty(preparation, "grant"));
            Assert.IsFalse(ContainsProperty(bundle, "grant"));
            Assert.IsTrue(translation.Bytes.Values.All(static bytes => bytes.Length > 0));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static void AssertBytesEqual(IReadOnlyDictionary<string, byte[]> expected, IReadOnlyDictionary<string, byte[]> actual)
    {
        CollectionAssert.AreEquivalent(expected.Keys.ToArray(), actual.Keys.ToArray());
        foreach (string path in expected.Keys) CollectionAssert.AreEqual(expected[path], actual[path], path);
    }

    private static JsonNode ReverseObjects(JsonNode node)
    {
        if (node is JsonObject document)
        {
            JsonObject result = new();
            foreach ((string name, JsonNode? value) in document.Reverse()) result[name] = value is null ? null : ReverseObjects(value);
            return result;
        }

        if (node is JsonArray array) return new JsonArray(array.Select(static item => item is null ? null : ReverseObjects(item)).ToArray());
        return node.DeepClone();
    }

    private static bool ContainsProperty(JsonNode node, string property)
    {
        if (node is JsonObject document)
        {
            if (document.ContainsKey(property)) return true;
            return document.Any(item => item.Value is not null && ContainsProperty(item.Value, property));
        }

        return node is JsonArray array && array.Any(item => item is not null && ContainsProperty(item, property));
    }
}
