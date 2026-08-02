using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
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

            for (int permutation = 0; permutation < 5; permutation++)
            {
                JsonObject permutedDocument = PermuteObjects(context.Handoff!.Document, permutation).AsObject();
                BoundHandoff permuted = new HandoffBinder().Bind(permutedDocument, requireComplete: true);
                Assert.AreEqual(context.Handoff.Digest, permuted.Digest);
                AssertBytesEqual(expected.Bytes, translator.Translate(permuted, PermuteObjects(context.WorkspaceLock, permutation + 1).AsObject()).Bytes);
            }
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
            AdapterTranslationProfile compatibility = AdapterCompatibility.Load().TranslationProfile;
            ContractAssertions.AssertValid("https://schemas.program-kit.dev/v1/software-definition-bundle.schema.json", bundle);
            ContractAssertions.AssertValid(ContractSchemaResources.PreparationRequestId, preparation);
            ContractAssertions.AssertValid(ContractAssertions.FactoryRequest, explanation);
            Assert.AreEqual(IntakePipeline.DocumentIdentityDigest(bundle), bundle["identity"]!["digest"]!.GetValue<string>());
            Assert.AreEqual(4, preparation["selections"]!.AsArray().Count);
            Assert.AreEqual(4, preparation["selections"]!.AsArray().Select(static item => item!["role"]!.GetValue<string>()).Distinct(StringComparer.Ordinal).Count());
            Assert.AreEqual("candidate-only", preparation["desiredEffect"]!.GetValue<string>());
            Assert.AreEqual(compatibility.BundleSchema, bundle["schema"]!.GetValue<string>());
            Assert.AreEqual(compatibility.PreparationSchema, preparation["schema"]!.GetValue<string>());
            Assert.AreEqual(compatibility.FactoryRequestSchema, explanation["schema"]!.GetValue<string>());
            Assert.AreEqual(compatibility.DefinitionMediaType, bundle["semanticRecords"]![0]!["mediaType"]!.GetValue<string>());
            Assert.IsTrue(preparation["selections"]!.AsArray().Any(item => CanonicalDocument.Encode(item!["selected"]!).SequenceEqual(CanonicalDocument.Encode(compatibility.Provider))));
            Assert.IsTrue(preparation["selections"]!.AsArray().Any(item => CanonicalDocument.Encode(item!["selected"]!).SequenceEqual(CanonicalDocument.Encode(compatibility.TargetProfile))));
            Assert.IsFalse(ContainsProperty(preparation, "grant"));
            Assert.IsFalse(ContainsProperty(bundle, "grant"));
            Assert.IsTrue(translation.Bytes.Values.All(static bytes => bytes.Length > 0));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Translation_rejects_definition_provider_and_profile_identity_outside_exact_compatibility()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true);
            DotNetHandoffTranslator translator = new();

            JsonObject wrongFamilyDocument = (JsonObject)context.Handoff!.Document.DeepClone();
            wrongFamilyDocument["definitionFamily"]!["digest"] = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
            BoundHandoff wrongFamily = new(wrongFamilyDocument, CanonicalDocument.Digest(wrongFamilyDocument), context.Handoff.TraceTargets);
            Assert.ThrowsExactly<InvalidOperationException>(() => translator.Translate(wrongFamily, context.WorkspaceLock));

            JsonObject wrongProviderLock = (JsonObject)context.WorkspaceLock.DeepClone();
            wrongProviderLock["selections"]![0]!["provider"]!["digest"] = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
            Assert.ThrowsExactly<InvalidOperationException>(() => translator.Translate(context.Handoff, wrongProviderLock));

            JsonObject wrongProfileLock = (JsonObject)context.WorkspaceLock.DeepClone();
            wrongProfileLock["selections"]![0]!["targetProfile"]!["name"] = "dotnet-unknown";
            Assert.ThrowsExactly<InvalidOperationException>(() => translator.Translate(context.Handoff, wrongProfileLock));
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

    private static JsonNode PermuteObjects(JsonNode node, int offset)
    {
        if (node is JsonObject document)
        {
            JsonObject result = new();
            var properties = document.ToArray();
            if (properties.Length > 0)
            {
                int rotation = offset % properties.Length;
                properties = properties.Skip(rotation).Concat(properties.Take(rotation)).ToArray();
                if ((offset & 1) == 1) Array.Reverse(properties);
            }
            foreach ((string name, JsonNode? value) in properties) result[name] = value is null ? null : PermuteObjects(value, offset + 1);
            return result;
        }

        if (node is JsonArray array) return new JsonArray(array.Select((item, index) => item is null ? null : PermuteObjects(item, offset + index + 1)).ToArray());
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
