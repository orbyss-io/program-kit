using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;
using Orbyss.ProgramKit.SpecKitAdapter.Translation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterEvidenceInvalidationTests
{
    [TestMethod]
    public void Unrelated_prose_and_named_block_whitespace_preserve_trace_and_claim_inputs()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true);
            TranslationResult translation = new DotNetHandoffTranslator().Translate(context.Handoff!, context.WorkspaceLock);
            JsonObject before = Sets(context, translation, context.Trace!);
            string specPath = Path.Combine(workspace, "tests", "Fixtures", "SpecKitAdapter", "Reference.Status", "spec.md");
            string spec = File.ReadAllText(specPath)
                .Replace("This prose is provenance only", "This unrelated prose changed on another branch", System.StringComparison.Ordinal)
                .Replace("feature exposes `GET /status` through\n`Reference.Status.Api` and delegates", "feature   exposes `GET /status`\n\nthrough `Reference.Status.Api` and   delegates", System.StringComparison.Ordinal);
            File.WriteAllText(specPath, spec);

            TraceResolution afterTrace = TraceResolver.Validate(workspace, context.Handoff!);
            CollectionAssert.AreEquivalent(context.Trace!.DependencyDigests.ToArray(), afterTrace.DependencyDigests.ToArray());
            JsonObject after = Sets(context, translation, afterTrace);
            Assert.AreEqual(0, TraceInvalidationEngine.ChangedClaims(before, after).Count);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Each_declared_input_invalidates_only_its_exact_downstream_closure()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true);
            TranslationResult translation = new DotNetHandoffTranslator().Translate(context.Handoff!, context.WorkspaceLock);
            JsonObject baseline = Sets(context, translation, context.Trace!);
            string definition = translation.Bytes.Keys.Single(path => path.EndsWith("/definitions/dotnet-component-api.json", System.StringComparison.Ordinal));
            string bundle = translation.Bytes.Keys.Single(path => path.EndsWith("/definitions/software-bundle.json", System.StringComparison.Ordinal));
            string prepare = translation.Bytes.Keys.Single(path => path.EndsWith("/requests/prepare.json", System.StringComparison.Ordinal));
            string explain = translation.Bytes.Keys.Single(path => path.EndsWith("/requests/explain.json", System.StringComparison.Ordinal));

            AssertChanged(baseline, Sets(context, translation, Changed(context.Trace!, "/maximumEffect")), "$claims", prepare);
            AssertChanged(baseline, Sets(context, translation, Changed(context.Trace!, "implementation:tests/Fixtures/SpecKitAdapter/Reference.Status/implementation/StatusFeature.cs")), "$claims", bundle, prepare, explain);
            AssertChanged(baseline, Sets(context, translation, Changed(context.Trace!, "/definition")), "$claims", definition, bundle, prepare, explain);

            AdapterCompatibilityDocument compatibility = AdapterCompatibility.Load();
            JsonObject compatibilityChanged = TraceInvalidationEngine.Build(context.Handoff!, context.Review!["digest"]!.GetValue<string>(), translation, context.Trace!, Different(compatibility.Digest));
            AssertChanged(baseline, compatibilityChanged, "$claims", definition, bundle, prepare, explain);

            JsonObject reviewChanged = TraceInvalidationEngine.Build(context.Handoff!, Different(context.Review!["digest"]!.GetValue<string>()), translation, context.Trace!, compatibility.Digest);
            AssertChanged(baseline, reviewChanged, "$claims");

            Dictionary<string, JsonObject> evidenceDocuments = new(translation.Documents, System.StringComparer.Ordinal)
            {
                [$"{translation.FeatureRoot}/results/prepare.json"] = new JsonObject { ["evidence"] = "first" },
            };
            TranslationResult firstEvidence = new(translation.FeatureRoot, evidenceDocuments, CanonicalArtifactWriter.Materialize(evidenceDocuments));
            JsonObject firstSets = Sets(context, firstEvidence, context.Trace!);
            evidenceDocuments[$"{translation.FeatureRoot}/results/prepare.json"]!["evidence"] = "second";
            TranslationResult secondEvidence = new(translation.FeatureRoot, evidenceDocuments, CanonicalArtifactWriter.Materialize(evidenceDocuments));
            AssertChanged(firstSets, Sets(context, secondEvidence, context.Trace!), $"{translation.FeatureRoot}/results/prepare.json");
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static JsonObject Sets(AdapterFeatureContext context, TranslationResult translation, TraceResolution trace)
    {
        AdapterCompatibilityDocument compatibility = AdapterCompatibility.Load();
        return TraceInvalidationEngine.Build(context.Handoff!, context.Review!["digest"]!.GetValue<string>(), translation, trace, compatibility.Digest);
    }

    private static TraceResolution Changed(TraceResolution trace, string key)
    {
        Dictionary<string, string> dependencies = new(trace.DependencyDigests, System.StringComparer.Ordinal)
        {
            [key] = Different(trace.DependencyDigests[key]),
        };
        return new TraceResolution(dependencies);
    }

    private static string Different(string digest) => digest == "sha256:" + new string('f', 64)
        ? "sha256:" + new string('e', 64)
        : "sha256:" + new string('f', 64);

    private static void AssertChanged(JsonObject before, JsonObject after, params string[] expected)
    {
        CollectionAssert.AreEquivalent(expected, TraceInvalidationEngine.ChangedClaims(before, after).ToArray());
    }
}
