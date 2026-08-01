using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Publication;
using Orbyss.ProgramKit.Kernel.Resolution;
using Orbyss.ProgramKit.Providers.DotNet;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class PublicationRecoveryAcceptanceTests
{
    [TestMethod]
    public void Interrupted_first_construction_is_untrusted_guided_and_recoverable_under_fresh_authority()
    {
        string workspace = TestRepository.CreateWorkspace(includeMirror: true);
        try
        {
            ProviderRegistry providers = new(new[] { new DotNetProvider() });
            IntakePipeline intake = new(providers);
            ResolutionEngine resolution = new(providers);
            ConstructOperation interruptedConstruction = new(
                intake,
                resolution,
                publisher: new RecoverablePublisher(new ThrowAtFirstLiveWrite()));
            OperationResult interrupted = interruptedConstruction.Execute(workspace, Path.Combine(workspace, "requests", "construct.json"));
            JsonObject fixture = JsonNode.Parse(File.ReadAllBytes(TestRepository.Fixture("Invalid/InterruptedPublication/fixture.json")))!.AsObject();
            JsonObject projected = OperationResultProjector.ToJson(interrupted);
            Assert.AreEqual(fixture["expectedOutcome"]!.GetValue<string>(), projected["outcome"]!.GetValue<string>());
            Assert.AreEqual(fixture["expectedEffectState"]!.GetValue<string>(), projected["effectState"]!.GetValue<string>());
            Assert.AreEqual(fixture["expectedDisposition"]!.GetValue<string>(), projected["primaryDisposition"]!.GetValue<string>());
            string[] interruptedIds = projected["diagnostics"]!["items"]!.AsArray().Select(static item => item!["id"]!.GetValue<string>()).ToArray();
            CollectionAssert.Contains(interruptedIds, fixture["expectedDiagnostic"]!.GetValue<string>());
            Assert.IsFalse(File.Exists(Path.Combine(workspace, ".program-kit", "construction-receipt.json")));

            var evaluated = TestRepository.RunCli(
                "evaluate", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "evaluate.json"), "--format", "json");
            Assert.AreEqual(3, evaluated.ExitCode, evaluated.StandardOutput + evaluated.StandardError);
            JsonObject evaluation = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, evaluated.StandardOutput);
            Assert.AreEqual("repair", evaluation["primaryDisposition"]!.GetValue<string>());
            JsonObject repair = evaluation["diagnostics"]!["items"]!.AsArray()
                .SelectMany(static item => item!["remediations"]!.AsArray())
                .Select(static item => item!["request"]!["document"]!.AsObject())
                .First();

            RepairAcceptanceTests.MaterializeFreshRepairAuthority(workspace, repair);
            string repairPath = Path.Combine(workspace, "requests", "publication-repair.json");
            File.WriteAllBytes(repairPath, Orbyss.ProgramKit.Kernel.Canonicalization.CanonicalJson.Encode(repair));
            var recovered = TestRepository.RunCli(
                "construct", "--workspace", workspace,
                "--request", repairPath, "--format", "json");
            Assert.AreEqual(0, recovered.ExitCode, recovered.StandardOutput + recovered.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, recovered.StandardOutput);
            Assert.AreEqual("committed", result["effectState"]!.GetValue<string>());

            var exact = TestRepository.RunCli(
                "evaluate", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "evaluate.json"), "--format", "json");
            Assert.AreEqual(0, exact.ExitCode, exact.StandardOutput + exact.StandardError);
            ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, exact.StandardOutput);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private sealed class ThrowAtFirstLiveWrite : IPublicationFaultInjector
    {
        public void Observe(string boundary, int completedOperations)
        {
            if (string.Equals(boundary, "live-write-completed", StringComparison.Ordinal))
            {
                throw new IOException($"Injected at {boundary}:{completedOperations}.");
            }
        }
    }
}
