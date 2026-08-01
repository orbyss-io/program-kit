using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class CliAndDiagnosticClosureTests
{
    [TestMethod]
    public void Public_cli_grammar_json_text_streams_and_exit_codes_are_closed()
    {
        string[][] invalidCommands =
        {
            new[] { "unknown", "--format", "json" },
            new[] { "explain", "--format", "json" },
            new[] { "help", "--workspace", ".", "--format", "json" },
            new[] { "version", "--request", "request.json", "--format", "json" },
            new[] { "explain", "--workspace", ".", "--request", "a", "--request", "b", "--format", "json" },
            new[] { "explain", "--workspace", ".", "--request", "a", "--unknown", "x", "--format", "json" },
            new[] { "explain", "--workspace", ".", "--request", "a", "--format", "yaml" },
            new[] { "explain", "--workspace", ".", "--request", "a", "--", "extra", "--format", "json" },
        };
        foreach (string[] arguments in invalidCommands)
        {
            var execution = TestRepository.RunCli(arguments);
            Assert.AreEqual(3, execution.ExitCode, string.Join(' ', arguments));
            Assert.AreEqual(string.Empty, execution.StandardError);
            bool jsonOutput = arguments.Select(static (value, index) => (value, index))
                .Any(item => item.value == "--format" && item.index + 1 < arguments.Length && arguments[item.index + 1] == "json");
            if (jsonOutput)
            {
                JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
                Assert.AreEqual("blocked", result["outcome"]!.GetValue<string>());
                Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
                Assert.IsFalse(execution.StandardOutput.EndsWith('\n'));
            }
            else
            {
                StringAssert.Contains(execution.StandardOutput, "outcome: blocked");
            }
        }

        foreach (string command in new[] { "help", "version" })
        {
            var json = TestRepository.RunCli(command, "--format", "json");
            Assert.AreEqual(0, json.ExitCode);
            Assert.AreEqual(string.Empty, json.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, json.StandardOutput);
            Assert.AreEqual(command, result["command"]!.GetValue<string>());
            Assert.IsNotNull(result["utility"]);

            var text = TestRepository.RunCli(command, "--format", "text");
            Assert.AreEqual(0, text.ExitCode);
            Assert.AreEqual(string.Empty, text.StandardError);
            StringAssert.Contains(text.StandardOutput, $"command: {command}");
            StringAssert.Contains(text.StandardOutput, "outcome: succeeded");
            Assert.IsTrue(text.StandardOutput.EndsWith('\n'));
        }

        var empty = TestRepository.RunCli();
        Assert.AreEqual(3, empty.ExitCode);
        Assert.AreEqual(string.Empty, empty.StandardError);
        StringAssert.Contains(empty.StandardOutput, "primary disposition: provide-input");
    }

    [TestMethod]
    public void Every_catalog_identity_projects_a_schema_valid_stable_diagnostic()
    {
        foreach (string id in DiagnosticCatalog.Entries.Keys.OrderBy(static item => item, StringComparer.Ordinal))
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                id,
                OperationPhase.Validation,
                "fixture-subject",
                "bounded cause",
                "bounded consequence",
                new Dictionary<string, SafeValue>(StringComparer.Ordinal) { ["value"] = new(SafeValueClassification.Public, SafeValueKind.Text, "bounded") });
            OperationResult result = OperationResultFactory.Failure(
                PublicCommand.Explain,
                OperationOutcome.Blocked,
                OperationPhase.Validation,
                EffectState.None,
                diagnostic.Disposition,
                new[] { diagnostic });
            JsonObject projected = OperationResultProjector.ToJson(result);
            ContractAssertions.AssertValid(ContractAssertions.OperationResult, projected);
            Assert.AreEqual(id, projected["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
            Assert.AreEqual(Disposition(diagnostic.Disposition), projected["diagnostics"]!["items"]![0]!["disposition"]!.GetValue<string>());
            Assert.IsNotNull(projected["diagnostics"]!["items"]![0]!["expected"]);
            Assert.IsNotNull(projected["diagnostics"]!["items"]![0]!["observed"]);
            Assert.IsTrue(projected["diagnostics"]!["items"]![0]!["remediations"]!.AsArray().Count > 0);
            Assert.AreEqual(id, diagnostic.Id);
            Assert.IsTrue(diagnostic.OccurrenceKey.StartsWith("sha256:", StringComparison.Ordinal));
        }
    }

    [TestMethod]
    public void Adversarial_diagnostic_values_never_cross_the_safe_projection_boundary()
    {
        string[] unsafeValues =
        {
            "password=hunter2",
            "token: abcdef",
            "Authorization: Bearer secret",
            "stdout: raw tool output",
            "System.InvalidOperationException at Service.Run(file.cs:42)",
            "C:\\Users\\someone\\private\\source.cs",
            "/home/someone/private/source.cs",
            new string('v', 600),
        };
        foreach (string unsafeValue in unsafeValues)
        {
            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.ExternalFailure,
                OperationPhase.Validation,
                unsafeValue,
                unsafeValue,
                unsafeValue,
                new Dictionary<string, SafeValue>(StringComparer.Ordinal) { ["observed"] = DisclosureFilter.Classify(unsafeValue) });
            JsonObject projected = OperationResultProjector.ToJson(OperationResultFactory.Failure(
                PublicCommand.Construct,
                OperationOutcome.Blocked,
                OperationPhase.Validation,
                EffectState.None,
                diagnostic.Disposition,
                new[] { diagnostic }));
            string json = projected.ToJsonString();
            Assert.IsFalse(json.Contains(unsafeValue, StringComparison.Ordinal));
            Assert.IsTrue(json.Contains("withheld", StringComparison.Ordinal) || unsafeValue.Length > 500);
            var failures = new StructuralSchemaValidator(new SchemaRegistry()).Validate(ContractAssertions.OperationResult, projected);
            Assert.AreEqual(0, failures.Count, $"{unsafeValue}{Environment.NewLine}{json}{Environment.NewLine}{string.Join(Environment.NewLine, failures)}");
        }
    }

    [TestMethod]
    public void Valid_explanation_matches_the_canonical_golden_digest()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            var execution = TestRepository.RunCli(
                "explain", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "explain.json"),
                "--format", "json");
            Assert.AreEqual(0, execution.ExitCode, execution.StandardOutput + execution.StandardError);
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
            string actual = CanonicalJson.Digest(result["explanation"]!);
            JsonObject golden = JsonNode.Parse(File.ReadAllBytes(TestRepository.Fixture("Golden/explanation/expected.json")))!.AsObject();
            Assert.AreEqual(golden["digest"]!.GetValue<string>(), actual, actual);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    private static string Disposition(PrimaryDisposition value) => value switch
    {
        PrimaryDisposition.ProvideInput => "provide-input",
        PrimaryDisposition.RequestApproval => "request-approval",
        PrimaryDisposition.Retry => "retry",
        PrimaryDisposition.Repair => "repair",
        PrimaryDisposition.Revise => "revise",
        PrimaryDisposition.Stop => "stop",
        _ => throw new ArgumentOutOfRangeException(nameof(value)),
    };
}
