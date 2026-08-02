using System;
using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
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
            Assert.AreEqual(8, context.Trace!.DependencyDigests.Count);
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
        AssertMutationFails("specs/003-reference-status/program-kit/handoff.yaml", static text => text.Replace("candidate-only", "committed", StringComparison.Ordinal), "handoff changed");
        AssertMutationFails("tests/Fixtures/SpecKitAdapter/Reference.Status/spec.md", static text => text.Replace("GET /status", "GET /health", StringComparison.Ordinal), "named block changed");
        AssertMutationFails("tests/Fixtures/SpecKitAdapter/Reference.Status/implementation/StatusFeature.cs", static text => text.Replace("\"ok\"", "\"healthy\"", StringComparison.Ordinal), "implementation changed");
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
            Assert.AreEqual(8, context.Trace!.DependencyDigests.Count);
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

    private static void AssertMutationFails(string logicalPath, Func<string, string> mutate, string because)
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            string path = Path.Combine(workspace, logicalPath.Replace('/', Path.DirectorySeparatorChar));
            File.WriteAllText(path, mutate(File.ReadAllText(path)));
            Assert.ThrowsExactly<InvalidDataException>(
                () => AdapterFeatureContextLoader.Load(workspace, SpecKitAdapterFixture.AdapterRequest("validate"), requireReviewedHandoff: true),
                because);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }
}
