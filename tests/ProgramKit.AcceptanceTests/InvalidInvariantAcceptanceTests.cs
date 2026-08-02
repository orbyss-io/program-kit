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
    [DataRow(true)]
    [DataRow(false)]
    public void Provider_failure_rolls_back_its_unsealed_candidate_and_the_exact_retry_can_complete(bool throwFailure)
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            RecoveringConstructionProvider provider = new(throwFailure);
            ProviderRegistry registry = new(new IFactoryProvider[] { provider });
            OperationExecutionTracker.Start(PublicCommand.Construct);
            ConstructOperation operation = new(
                new IntakePipeline(registry),
                new ResolutionEngine(registry));
            OperationResult failed = operation.Execute(
                    workspace,
                    Path.Combine(workspace, "requests", "construct.json"));
            JsonObject projected = OperationResultProjector.ToJson(failed);
            ContractAssertions.AssertValid(ContractAssertions.OperationResult, projected);

            Assert.AreEqual("blocked", projected["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", projected["effectState"]!.GetValue<string>());
            Assert.AreEqual("retry", projected["primaryDisposition"]!.GetValue<string>());
            string expectedDiagnostic = throwFailure ? "program-kit.kernel/PKEXT0001" : "program-kit.provider.dotnet/PKDOT0006";
            Assert.AreEqual(expectedDiagnostic, projected["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
            JsonObject remediation = projected["diagnostics"]!["items"]![0]!["remediations"]![0]!.AsObject();
            CollectionAssert.AreEqual(
                new[] { "construct", "--workspace", ".", "--request", "requests/construct.json", "--format", "json" },
                remediation["request"]!["arguments"]!.AsArray().Select(static item => item!.GetValue<string>()).ToArray());
            CollectionAssert.Contains(
                remediation["authorityRequired"]!.AsArray().Select(static item => item!.GetValue<string>()).ToArray(),
                "current-exact-authority");
            if (!throwFailure)
            {
                JsonObject parameters = projected["diagnostics"]!["items"]![0]!["parameters"]!.AsObject();
                Assert.AreEqual("dotnet", parameters["tool"]!["value"]!.GetValue<string>());
                Assert.AreEqual("1", parameters["exitCode"]!["value"]!.GetValue<string>());
                Assert.AreEqual($"sha256:{new string('1', 64)}", parameters["observationDigest"]!["value"]!.GetValue<string>());
                Assert.AreEqual("NU1000", parameters["diagnosticCodes"]!["value"]!.GetValue<string>());
            }
            Assert.IsNotNull(failed.ConstructionIdentity);
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates", failed.ConstructionIdentity!["sha256:".Length..])));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates")));
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, "products")));
            Assert.IsFalse(File.Exists(Path.Combine(workspace, ".program-kit", "construction-receipt.json")));

            OperationExecutionTracker.Start(PublicCommand.Construct);
            OperationResult retried = operation.Execute(
                workspace,
                Path.Combine(workspace, "requests", "construct.json"));
            Assert.AreEqual(OperationOutcome.Succeeded, retried.Outcome);
            Assert.AreEqual(EffectState.Committed, retried.EffectState);
            Assert.AreEqual(PrimaryDisposition.Complete, retried.PrimaryDisposition);
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

    [TestMethod]
    public void Missing_declared_dependency_mirror_is_unavailable_before_candidate_creation()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            var execution = TestRepository.RunCli(
                "construct", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "construct.json"),
                "--format", "json");
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);

            Assert.AreEqual("blocked", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
            Assert.AreEqual("stop", result["primaryDisposition"]!.GetValue<string>());
            Assert.AreEqual("program-kit.kernel/PKEXT0002", result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates")));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private sealed class RecoveringConstructionProvider : IIntakeMappingProvider, IConstructionProvider, IEvaluationProvider
    {
        private readonly DotNetProvider inner = new();
        private readonly bool throwFailure;
        private int attempts;

        public RecoveringConstructionProvider(bool throwFailure) => this.throwFailure = throwFailure;

        public ProviderManifest Manifest => inner.Manifest;

        public Task<ProviderIntakeResult> MapAsync(ProviderIntakeContext context) => inner.MapAsync(context);

        public Task<ProviderConstructionResult> ConstructAsync(ProviderConstructionContext context)
        {
            attempts++;
            if (attempts > 1)
            {
                return inner.ConstructAsync(context);
            }

            if (throwFailure)
            {
                throw new InvalidOperationException("Raw provider exception that must remain undisclosed.");
            }

            return Task.FromResult(new ProviderConstructionResult(
                Array.Empty<ProviderArtifact>(),
                new[]
                {
                    new JsonObject
                    {
                        ["tool"] = "dotnet",
                        ["observationDigest"] = $"sha256:{new string('1', 64)}",
                        ["diagnosticCodes"] = new JsonArray("NU1000"),
                        ["exitCode"] = 1,
                    },
                },
                new[] { "program-kit.provider.dotnet/PKDOT0006" },
                false));
        }

        public Task<ProviderEvaluationResult> EvaluateAsync(ProviderEvaluationContext context) => inner.EvaluateAsync(context);
    }
}
