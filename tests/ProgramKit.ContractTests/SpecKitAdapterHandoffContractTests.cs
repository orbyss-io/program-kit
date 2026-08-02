using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterHandoffContractTests
{
    [TestMethod]
    public void Exact_config_handoff_review_and_field_trace_bind_to_current_approved_meaning()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            JsonObject request = SpecKitAdapterFixture.AdapterRequest("validate");
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, request, requireReviewedHandoff: true);
            Assert.IsTrue(context.Applicability.Active);
            Assert.AreEqual(ActivationMode.Required, context.Applicability.Mode);
            Assert.AreEqual(Applicability.Applicable, context.Applicability.Applicability);
            Assert.AreEqual("dotnet-default", context.Handoff!.Document["effectiveSelection"]!["alias"]!.GetValue<string>());
            Assert.AreEqual(14, context.Trace!.DependencyDigests.Count);
            CollectionAssert.AreEquivalent(
                new[] { "compatibility-fixed", "human-decision", "plan-decision", "spec-block", "task-row" },
                context.Handoff.Document["trace"]!.AsArray().Select(static node => node!["sourceKind"]!.GetValue<string>()).Distinct(StringComparer.Ordinal).ToArray());
            Assert.AreEqual(context.Handoff.Digest, context.Review!["handoff"]!["digest"]!.GetValue<string>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Changed_handoff_named_block_or_implementation_stales_exact_review_or_trace()
    {
        AssertMutationFails("specs/003-reference-status/program-kit/handoff.yaml", static text => text.Replace("candidate-only", "committed", StringComparison.Ordinal), AdapterFailureKind.InvalidReview, "handoff changed");
        AssertMutationFails("tests/Fixtures/SpecKitAdapter/Reference.Status/spec.md", static text => text.Replace("GET /status", "GET /health", StringComparison.Ordinal), AdapterFailureKind.StaleTrace, "named block changed");
        AssertMutationFails("tests/Fixtures/SpecKitAdapter/Reference.Status/plan.md", static text => text.Replace("accountable intent owner", "feature owner", StringComparison.Ordinal), AdapterFailureKind.StaleTrace, "plan decision changed");
        AssertMutationFails("tests/Fixtures/SpecKitAdapter/Reference.Status/tasks.md", static text => text.Replace("factory-applicable", "factory eligible", StringComparison.Ordinal), AdapterFailureKind.StaleTrace, "task row changed");
        AssertMutationFails("tests/Fixtures/SpecKitAdapter/Reference.Status/implementation/StatusFeature.cs", static text => text.Replace("\"operational\"", "\"degraded\"", StringComparison.Ordinal), AdapterFailureKind.StaleTrace, "implementation changed");
    }

    [TestMethod]
    public void Unrelated_prose_outside_the_named_block_does_not_stale_reviewed_meaning()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            string spec = Path.Combine(workspace, "tests", "Fixtures", "SpecKitAdapter", "Reference.Status", "spec.md");
            File.AppendAllText(spec, "\nNon-semantic reviewer note.\n");
            AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true);
            Assert.AreEqual(14, context.Trace!.DependencyDigests.Count);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Ambiguous_blocks_incomplete_meaning_and_heuristic_or_authority_fields_are_rejected()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            JsonObject handoff = RestrictedYaml.Parse(File.ReadAllText(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff.yaml")));
            handoff["unresolved"]!.AsArray().Add("contract name");
            Assert.ThrowsExactly<InvalidDataException>(() => new HandoffBinder().Bind(handoff, requireComplete: true));

            handoff["unresolved"] = new JsonArray();
            handoff["trace"]!.AsArray().RemoveAt(0);
            Assert.ThrowsExactly<InvalidDataException>(() => new HandoffBinder().Bind(handoff, requireComplete: true));

            handoff = RestrictedYaml.Parse(File.ReadAllText(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff.yaml")));
            BoundHandoff bound = new HandoffBinder().Bind(handoff, requireComplete: true);
            JsonObject rejectedReview = CanonicalDocument.Parse(File.ReadAllBytes(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff-review.json"))).AsObject();
            rejectedReview["decision"] = "rejected";
            Assert.ThrowsExactly<InvalidDataException>(() => HandoffReviewValidator.Validate(workspace, bound, rejectedReview));

            handoff = (JsonObject)handoff.DeepClone();
            handoff["trace"]![0]!["sourceKind"] = "free-prose";
            BoundHandoff heuristic = new HandoffBinder().Bind(handoff, requireComplete: true);
            Assert.ThrowsExactly<InvalidDataException>(() => TraceResolver.Validate(workspace, heuristic));

            handoff = RestrictedYaml.Parse(File.ReadAllText(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff.yaml")));
            handoff["prompt"] = "infer missing names";
            Assert.ThrowsExactly<InvalidDataException>(() => new HandoffBinder().Bind(handoff, requireComplete: true));

            handoff.Remove("prompt");
            handoff["grant"] = new JsonObject();
            Assert.ThrowsExactly<InvalidDataException>(() => new HandoffBinder().Bind(handoff, requireComplete: true));

            string ambiguous = File.ReadAllText(SpecKitAdapterFixture.RepositoryFixture("Invalid/Handoff/ambiguous-source.md"));
            Assert.ThrowsExactly<InvalidDataException>(() => TraceResolver.ExtractNamedBlock(ambiguous, "FR-AMBIGUOUS"));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void No_code_or_explicitly_disabled_feature_is_non_applicable_without_loading_a_handoff()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            string configPath = Path.Combine(workspace, AdapterConfigResolver.ProjectConfigPath.Replace('/', Path.DirectorySeparatorChar));
            string config = File.ReadAllText(configPath).Replace("applicability: applicable", "applicability: not-applicable", StringComparison.Ordinal);
            File.WriteAllText(configPath, config);
            JsonObject result = ValidateCommand.Execute(workspace, SpecKitAdapterFixture.AdapterRequest("validate"));
            Assert.AreEqual("not-applicable", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Configuration_and_selection_precedence_are_exact_and_have_no_ambient_default()
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            string configPath = Path.Combine(workspace, AdapterConfigResolver.ProjectConfigPath.Replace('/', Path.DirectorySeparatorChar));
            ResolvedAdapterConfig config = new AdapterConfigResolver().Resolve(workspace, AdapterConfigResolver.ProjectConfigPath);
            JsonObject lockDocument = CanonicalDocument.Parse(File.ReadAllBytes(Path.Combine(workspace, "program-kit.lock.json"))).AsObject();
            EffectiveSelection explicitSelection = SelectionResolver.Resolve(config.Document, SpecKitAdapterFixture.FeatureKey, lockDocument);
            Assert.AreEqual("feature-override", explicitSelection.Source);

            JsonObject inheritedConfig = (JsonObject)config.Document.DeepClone();
            inheritedConfig["activation"]!["features"]![SpecKitAdapterFixture.FeatureKey]!.AsObject().Remove("selection");
            EffectiveSelection inherited = SelectionResolver.Resolve(inheritedConfig, SpecKitAdapterFixture.FeatureKey, lockDocument);
            Assert.AreEqual("workspace-lock-default", inherited.Source);

            JsonObject noDefaultLock = (JsonObject)lockDocument.DeepClone();
            noDefaultLock.Remove("defaultSelection");
            Assert.ThrowsExactly<InvalidDataException>(() => SelectionResolver.Resolve(inheritedConfig, SpecKitAdapterFixture.FeatureKey, noDefaultLock));

            ApplicabilityResolution absent = ApplicabilityResolver.Resolve(config.Document, "unconfigured-feature");
            Assert.AreEqual(ActivationMode.Assist, absent.Mode);
            Assert.AreEqual(Applicability.Unresolved, absent.Applicability);
            Assert.IsFalse(absent.Active);

            File.WriteAllText(Path.Combine(workspace, AdapterConfigResolver.LocalConfigPath.Replace('/', Path.DirectorySeparatorChar)), "ignored: true");
            ResolvedAdapterConfig withAmbient = new AdapterConfigResolver().Resolve(workspace, AdapterConfigResolver.ProjectConfigPath);
            Assert.IsTrue(withAmbient.AmbientLayerPresent);
            Assert.AreEqual(CanonicalDocument.Digest(config.Document), CanonicalDocument.Digest(withAmbient.Document));
            Assert.IsTrue(File.Exists(configPath));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static void AssertMutationFails(string logicalPath, Func<string, string> mutate, AdapterFailureKind expected, string because)
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            string path = Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            File.WriteAllText(path, mutate(File.ReadAllText(path)));
            AdapterBoundaryException exception = Assert.ThrowsExactly<AdapterBoundaryException>(
                () => AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true),
                because);
            Assert.AreEqual(expected, exception.Kind);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }
}
