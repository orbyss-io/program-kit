using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Tests.Diagnostics;

[TestClass]
public sealed class DisclosureTests
{
    [TestMethod]
    public void Adversarial_values_are_withheld_before_the_authoritative_projection()
    {
        string[] unsafeValues =
        {
            "password=hunter2",
            "C:\\Users\\consumer\\protected\\authority.json",
            "rm -rf ./workspace",
            "stdout: bearer private-token",
            "stderr: connectionString=private",
            "System.InvalidOperationException: private detail",
            "at Consumer.Secret.Run(C:\\src\\Secret.cs:42)",
        };
        foreach (string unsafeValue in unsafeValues)
        {
            SafeValue classified = DisclosureFilter.PublicText(unsafeValue);
            Assert.AreEqual(SafeValueClassification.Withheld, classified.Classification, unsafeValue);
            Assert.AreEqual(SafeValueKind.Redacted, classified.ValueKind, unsafeValue);
            Assert.IsNull(classified.Value, unsafeValue);
            Assert.IsNotNull(classified.PolicyReference, unsafeValue);

            Diagnostic diagnostic = DiagnosticFactory.Create(
                DiagnosticIds.ExternalFailure,
                OperationPhase.Validation,
                DisclosureFilter.PublicText("external-provider"),
                DisclosureFilter.Withhold(unsafeValue, "unsafe-observation"),
                DisclosureFilter.PublicText("The external observation is withheld."),
                new Dictionary<string, SafeValue>(StringComparer.Ordinal)
                {
                    ["observed"] = classified,
                });
            JsonObject projected = OperationResultProjector.ToJson(OperationResultFactory.Failure(
                PublicCommand.Construct,
                OperationOutcome.Blocked,
                OperationPhase.Validation,
                EffectState.None,
                PrimaryDisposition.Retry,
                new[] { diagnostic }));
            string json = projected.ToJsonString();
            Assert.IsFalse(json.Contains(unsafeValue, StringComparison.Ordinal), unsafeValue);
            Assert.IsTrue(json.Contains("withheld", StringComparison.Ordinal), unsafeValue);
            ContractAssertions.AssertValid(ContractAssertions.OperationResult, projected);
        }
    }

    [TestMethod]
    public void Secret_derived_fingerprints_require_caller_classification_and_are_not_reversible()
    {
        const string derivedFingerprint = "sha256:4b7bc5e7c31edc11d8a7d6f92d20d989cc86ec64b6f9a7e15338b18f7b6c0209";
        SafeValue withheld = DisclosureFilter.Withhold(derivedFingerprint, "secret-derived-fingerprint");
        Diagnostic diagnostic = DiagnosticFactory.Create(
            DiagnosticIds.InvalidInput,
            OperationPhase.Validation,
            DisclosureFilter.PublicText("request"),
            DisclosureFilter.PublicText("A restricted value was supplied."),
            DisclosureFilter.PublicText("The restricted value is not echoed."),
            new Dictionary<string, SafeValue>(StringComparer.Ordinal) { ["fingerprint"] = withheld });
        string json = OperationResultProjector.ToJson(OperationResultFactory.Failure(
            PublicCommand.Explain,
            OperationOutcome.Blocked,
            OperationPhase.Validation,
            EffectState.None,
            PrimaryDisposition.Revise,
            new[] { diagnostic })).ToJsonString();

        Assert.IsFalse(json.Contains(derivedFingerprint, StringComparison.Ordinal));
        Assert.IsTrue(json.Contains("secret-derived-fingerprint", StringComparison.Ordinal));
    }

    [TestMethod]
    public void Opaque_unknown_cli_tokens_are_never_echoed_by_parse_diagnostics()
    {
        const string opaque = "sha256:4b7bc5e7c31edc11d8a7d6f92d20d989cc86ec64b6f9a7e15338b18f7b6c0209";
        string[][] invocations =
        {
            new[] { opaque, "--format", "json" },
            new[] { "help", opaque, "--format", "json" },
            new[] { "help", $"--{opaque}", "--format", "json" },
        };

        foreach (string[] invocation in invocations)
        {
            var execution = TestRepository.RunCli(invocation);
            Assert.AreNotEqual(0, execution.ExitCode);
            Assert.AreEqual(string.Empty, execution.StandardError);
            Assert.IsFalse(execution.StandardOutput.Contains(opaque, StringComparison.Ordinal), execution.StandardOutput);
            ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
        }
    }
    [TestMethod]
    public void Verbose_progress_and_unknown_cli_input_stay_on_the_safe_machine_channel()
    {
        string workspace = TestRepository.CreateWorkspace();
        try
        {
            var execution = TestRepository.RunCli(
                "explain", "--workspace", workspace,
                "--request", Path.Combine(workspace, "requests", "explain.json"),
                "--format", "json",
                "--verbose", "password=hunter2",
                "--progress", "stderr: private-token");
            Assert.AreNotEqual(0, execution.ExitCode);
            Assert.AreEqual(string.Empty, execution.StandardError);
            Assert.IsFalse(execution.StandardOutput.Contains("hunter2", StringComparison.OrdinalIgnoreCase));
            Assert.IsFalse(execution.StandardOutput.Contains("private-token", StringComparison.OrdinalIgnoreCase));
            ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, execution.StandardOutput);
        }
        finally
        {
            TestRepository.DeleteWorkspace(workspace);
        }
    }

    [TestMethod]
    public void Independent_fallback_is_fixed_schema_valid_and_environment_secret_independent()
    {
        const string secret = "fallback-password=hunter2";
        string? original = Environment.GetEnvironmentVariable("PROGRAM_KIT_TEST_SECRET");
        try
        {
            Environment.SetEnvironmentVariable("PROGRAM_KIT_TEST_SECRET", secret);
            string first = RenderFallback();
            Environment.SetEnvironmentVariable("PROGRAM_KIT_TEST_SECRET", "different-secret");
            string second = RenderFallback();

            Assert.AreEqual(first, second);
            Assert.IsFalse(first.Contains(secret, StringComparison.OrdinalIgnoreCase));
            JsonObject result = ContractAssertions.ParseAndValidate(ContractAssertions.OperationResult, first);
            Assert.AreEqual("faulted", result["outcome"]!.GetValue<string>());
            Assert.AreEqual("indeterminate", result["effectState"]!.GetValue<string>());
            Assert.AreEqual("stop", result["diagnostics"]!["items"]![0]!["disposition"]!.GetValue<string>());
        }
        finally
        {
            Environment.SetEnvironmentVariable("PROGRAM_KIT_TEST_SECRET", original);
        }
    }

    private static string RenderFallback()
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
        return Encoding.UTF8.GetString(output.ToArray());
    }
}
