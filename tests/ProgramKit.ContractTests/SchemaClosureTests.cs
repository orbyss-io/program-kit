using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SchemaClosureTests
{
    [TestMethod]
    public void Embedded_public_schemas_are_byte_identical_to_the_design_contracts()
    {
        foreach ((string name, string embedded) in ContractSchemaResources.ReadAll())
        {
            string owningFeature = name.StartsWith("session-", StringComparison.Ordinal)
                ? "002-session-integration-proof"
                : "001-status-component-api";
            string designPath = Path.Combine(TestRepository.Root, "specs", owningFeature, "contracts", name);
            Assert.IsTrue(File.Exists(designPath), designPath);
            Assert.AreEqual(File.ReadAllText(designPath), embedded, name);
        }
    }

    [TestMethod]
    public void Factory_request_conditionals_and_closed_objects_are_enforced_offline()
    {
        JsonObject valid = JsonNode.Parse(File.ReadAllText(TestRepository.Fixture("Valid/requests/construct.json")))!.AsObject();
        ContractAssertions.AssertValid(ContractAssertions.FactoryRequest, valid);

        JsonObject extra = (JsonObject)valid.DeepClone();
        extra["unexpected"] = true;
        AssertInvalid(ContractAssertions.FactoryRequest, extra);

        JsonObject noMode = (JsonObject)valid.DeepClone();
        noMode.Remove("constructionMode");
        AssertInvalid(ContractAssertions.FactoryRequest, noMode);

        JsonObject noAuthority = (JsonObject)valid.DeepClone();
        noAuthority.Remove("authorityGrant");
        AssertInvalid(ContractAssertions.FactoryRequest, noAuthority);

        JsonObject noExpectedState = (JsonObject)valid.DeepClone();
        noExpectedState.Remove("expectedState");
        AssertInvalid(ContractAssertions.FactoryRequest, noExpectedState);
    }

    [TestMethod]
    public void Missing_input_result_aggregates_known_fields_and_conforms_to_the_public_contract()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            string request = Path.Combine(workspace, "requests", "incomplete.json");
            File.WriteAllText(request, "{\"schema\":\"program-kit.factory-request/v1\",\"canonicalProfile\":\"program-kit.canonical-json/v1\",\"operation\":\"explain\"}");
            var execution = TestRepository.RunCli("explain", "--workspace", workspace, "--request", request, "--format", "json");
            Assert.AreEqual(2, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            JsonArray missing = result["continuation"]!["missingInputs"]!.AsArray();
            Assert.IsTrue(missing.Count >= 5, "Independently known missing input should be aggregated in one continuation.");
            Assert.AreEqual("needs-input", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Diagnostic_truncation_projects_a_schema_valid_cursor()
    {
        Diagnostic[] diagnostics = Enumerable.Range(0, 101).Select(index => DiagnosticFactory.Create(
            DiagnosticIds.InvalidInput,
            OperationPhase.Validation,
            DisclosureFilter.PublicText($"subject-{index:D3}"),
            DisclosureFilter.PublicText("invalid"),
            DisclosureFilter.PublicText("revise"))).ToArray();
        OperationResult result = OperationResultFactory.Failure(
            PublicCommand.Construct,
            OperationOutcome.Blocked,
            OperationPhase.Validation,
            EffectState.None,
            PrimaryDisposition.Revise,
            diagnostics);
        JsonObject projected = OperationResultProjector.ToJson(result);
        ContractAssertions.AssertValid(ContractAssertions.OperationResult, projected);
        Assert.AreEqual(1, projected["diagnostics"]!["omitted"]!.GetValue<int>());
        Assert.IsNotNull(projected["diagnostics"]!["cursor"]);
    }

    [TestMethod]
    public void Independent_fallback_reports_the_proven_phase_and_effect_and_validates()
    {
        string configuration = new DirectoryInfo(AppContext.BaseDirectory).Parent?.Name
            ?? throw new InvalidOperationException("Test configuration unavailable.");
        string cliPath = Path.Combine(TestRepository.Root, "src", "ProgramKit.Cli", "bin", configuration, "net10.0", "program-kit.dll");
        Assembly cli = Assembly.LoadFrom(cliPath);
        Type writer = cli.GetType("Orbyss.ProgramKit.Cli.Rendering.FallbackResultWriter", throwOnError: true)!;
        MethodInfo write = writer.GetMethod("Write", BindingFlags.Public | BindingFlags.Static | BindingFlags.NonPublic)
            ?? throw new MissingMethodException(writer.FullName, "Write");
        using MemoryStream output = new();
        write.Invoke(null, new object[] { PublicCommand.Construct, OperationPhase.Publication, EffectState.Indeterminate, output });
        JsonObject result = ContractAssertions.ParseAndValidate(
            ContractAssertions.OperationResult,
            System.Text.Encoding.UTF8.GetString(output.ToArray()));
        Assert.AreEqual("publication", result["furthestPhase"]!.GetValue<string>());
        Assert.AreEqual("indeterminate", result["effectState"]!.GetValue<string>());
        Assert.AreEqual("program-kit.kernel/PKINT0001", result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.IsFalse(result["operationContract"]!["digest"]!.GetValue<string>().EndsWith(new string('0', 64), StringComparison.Ordinal));
    }

    private static void AssertInvalid(string schemaId, JsonObject document)
    {
        var failures = new StructuralSchemaValidator(new SchemaRegistry()).Validate(schemaId, document);
        Assert.IsTrue(failures.Count > 0, "Expected exact schema rejection.");
    }
}
