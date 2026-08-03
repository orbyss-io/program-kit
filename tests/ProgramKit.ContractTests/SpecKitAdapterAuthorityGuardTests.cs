using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.SpecKitAdapter.Commands;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SpecKitAdapterAuthorityGuardTests
{
    [TestMethod]
    [DataRow("missing-grant")]
    [DataRow("no-effect")]
    [DataRow("broader-effect")]
    public void Adapter_construct_refuses_absent_or_inexact_authority_before_any_public_invocation(string scenario)
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            JsonObject request = SpecKitAdapterFixture.AdapterRequest("construct");
            request["requestedEffect"] = scenario switch
            {
                "missing-grant" => "candidate-only",
                "no-effect" => "none",
                "broader-effect" => "committed",
                _ => throw new ArgumentOutOfRangeException(nameof(scenario)),
            };
            if (scenario != "missing-grant") request["grant"] = GrantReference();
            RefusingInvoker invoker = new();

            JsonObject result = new ConstructCommand(invoker).Execute(workspace, request);

            Assert.AreEqual(scenario == "missing-grant" ? "needs-input" : "blocked", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("request-approval", result["primaryDisposition"]!.GetValue<string>());
            Assert.AreEqual(0, invoker.Commands.Count, "Authority refusal must happen before the adapter launches Program Kit.");
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates")));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    [DataRow("caller-grant")]
    [DataRow("handoff-review")]
    public void Adapter_construct_forwards_only_the_exact_caller_object_and_never_records_or_selects_authority(string scenario)
    {
        string workspace = SpecKitAdapterFixture.CreateWorkspace();
        try
        {
            JsonObject supplied = scenario == "caller-grant"
                ? GrantReference()
                : CanonicalDocument.Parse(File.ReadAllBytes(Path.Combine(workspace, "specs", SpecKitAdapterFixture.FeatureKey, "program-kit", "handoff-review.json"))).AsObject();
            JsonObject request = SpecKitAdapterFixture.AdapterRequest("construct");
            request["requestedEffect"] = "candidate-only";
            request["grant"] = supplied.DeepClone();
            RecordingPublicCliInvoker invoker = new();

            JsonObject result = new ConstructCommand(invoker).Execute(workspace, request);

            CollectionAssert.AreEqual(new[] { "prepare", "explain", "construct" }, invoker.Commands.ToArray());
            Assert.IsNotNull(invoker.ConstructRequest);
            Assert.IsTrue(JsonNode.DeepEquals(supplied, invoker.ConstructRequest!["authorityGrant"]), "The adapter must copy, not issue, select, broaden, or reinterpret the caller object.");
            Assert.AreEqual("blocked", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", result["programKitResult"]!["effectState"]!.GetValue<string>());
            Assert.IsFalse(Directory.Exists(Path.Combine(workspace, ".program-kit", "candidates")));
            Assert.IsFalse(invoker.Commands.Contains("authority"));
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static JsonObject GrantReference() => new()
    {
        ["identity"] = new JsonObject
        {
            ["authority"] = "consumer.reference",
            ["kind"] = "authority-grant",
            ["name"] = "caller-selected-grant",
            ["revision"] = "1.0.0",
            ["digest"] = "sha256:" + new string('a', 64),
        },
        ["mediaType"] = "application/vnd.program-kit.authority-grant+json",
        ["logicalPath"] = ".program-kit/authority/caller-selected.grant.json",
        ["digest"] = "sha256:" + new string('a', 64),
        ["ownership"] = "consumer-owned",
    };

    private sealed class RefusingInvoker : IPublicProgramKitInvoker
    {
        public List<string> Commands { get; } = new();

        public JsonObject Invoke(string workspaceRoot, string command, string requestLogicalPath)
        {
            Commands.Add(command);
            throw new AssertFailedException("The adapter invoked Program Kit before admitting exact caller authority.");
        }
    }

    private sealed class RecordingPublicCliInvoker : IPublicProgramKitInvoker
    {
        public List<string> Commands { get; } = new();
        public JsonObject? ConstructRequest { get; private set; }

        public JsonObject Invoke(string workspaceRoot, string command, string requestLogicalPath)
        {
            Commands.Add(command);
            string request = Path.Combine(workspaceRoot, requestLogicalPath.Replace('/', Path.DirectorySeparatorChar));
            if (command == "construct") ConstructRequest = CanonicalDocument.Parse(File.ReadAllBytes(request)).AsObject();
            var execution = TestRepository.RunCli(command, "--workspace", workspaceRoot, "--request", request, "--format", "json");
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            int expectedExitCode = result["outcome"]!.GetValue<string>() switch
            {
                "succeeded" => 0,
                "faulted" => 1,
                "needs-input" => 2,
                "blocked" => 3,
                "cancelled" => 130,
                _ => -1,
            };
            Assert.AreEqual(expectedExitCode, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            return CanonicalDocument.Parse(Encoding.UTF8.GetBytes(execution.StandardOutput)).AsObject();
        }
    }
}
