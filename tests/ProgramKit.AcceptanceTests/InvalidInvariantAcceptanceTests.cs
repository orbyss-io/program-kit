using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Resolution;
using Orbyss.ProgramKit.Providers.DotNet;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class InvalidInvariantAcceptanceTests
{
    [TestMethod]
    public void Live_collision_fixture_stops_before_product_publication_or_admission()
    {
        JsonObject fixture = Fixture("LiveCollision");
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            string state = Path.Combine(workspace, ".program-kit");
            Directory.CreateDirectory(state);
            string sentinel = Path.Combine(state, "resolution.lock.json");
            File.WriteAllText(sentinel, "consumer-collision");

            var execution = TestRepository.RunCli(
                "construct", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "construct.json"),
                "--format", "json");
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);

            AssertFixture(result, fixture);
            Assert.AreEqual("consumer-collision", File.ReadAllText(sentinel));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, "products")));
            Assert.IsFalse(File.Exists(Path.Combine(state, "construction-receipt.json")));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Stale_precondition_fixture_evaluates_without_mutation()
    {
        JsonObject fixture = Fixture("StalePrecondition");
        string workspace = ConstructWorkspace();
        try
        {
            File.AppendAllText(Path.Combine(workspace, ".program-kit", "resolution.lock.json"), " ");
            string before = TestRepository.DigestTree(workspace);

            var execution = TestRepository.RunCli(
                "evaluate", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "evaluate.json"),
                "--format", "json");
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);

            AssertFixture(result, fixture);
            Assert.AreEqual(before, TestRepository.DigestTree(workspace));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Provider_failure_fixture_is_bounded_to_candidate_state()
    {
        JsonObject fixture = Fixture("ProviderFailure");
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            ThrowingConstructionProvider provider = new();
            ProviderRegistry registry = new(new IFactoryProvider[] { provider });
            OperationExecutionTracker.Start(PublicCommand.Construct);
            OperationResult result = new ConstructOperation(
                new IntakePipeline(registry),
                new ResolutionEngine(registry)).Execute(
                    workspace,
                    Path.Combine(workspace, "requests", "construct.json"));

            AssertFixture(OperationResultProjector.ToJson(result), fixture);
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, "products")));
            Assert.IsFalse(File.Exists(Path.Combine(workspace, ".program-kit", "construction-receipt.json")));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static string ConstructWorkspace()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        var execution = TestRepository.RunCli(
            "construct", "--workspace", workspace,
            "--request", Path.Combine(workspace, "requests", "construct.json"),
            "--format", "json");
        if (execution.ExitCode != 0)
        {
            TestRepository.DeleteWorkspace(workspace);
            Assert.Fail(execution.StandardOutput + execution.StandardError);
        }

        return workspace;
    }

    private static JsonObject Fixture(string name) =>
        JsonNode.Parse(File.ReadAllBytes(TestRepository.Fixture($"Invalid/{name}/fixture.json")))!.AsObject();

    private static void AssertFixture(JsonObject result, JsonObject fixture)
    {
        Assert.AreEqual(fixture["expectedOutcome"]!.GetValue<string>(), result["outcome"]!.GetValue<string>());
        Assert.AreEqual(fixture["expectedEffectState"]!.GetValue<string>(), result["effectState"]!.GetValue<string>());
        Assert.AreEqual(fixture["expectedDisposition"]!.GetValue<string>(), result["primaryDisposition"]!.GetValue<string>());
        string[] diagnostics = result["diagnostics"]!["items"]!.AsArray()
            .Select(static item => item!["id"]!.GetValue<string>())
            .ToArray();
        CollectionAssert.Contains(diagnostics, fixture["expectedDiagnostic"]!.GetValue<string>());
    }

    private sealed class ThrowingConstructionProvider : IIntakeMappingProvider, IConstructionProvider, IEvaluationProvider
    {
        private readonly DotNetProvider inner = new();

        public ProviderManifest Manifest => inner.Manifest;

        public Task<ProviderIntakeResult> MapAsync(ProviderIntakeContext context) => inner.MapAsync(context);

        public Task<ProviderConstructionResult> ConstructAsync(ProviderConstructionContext context) =>
            throw new InvalidOperationException("Raw provider exception that must remain undisclosed.");

        public Task<ProviderEvaluationResult> EvaluateAsync(ProviderEvaluationContext context) => inner.EvaluateAsync(context);
    }
}
