using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionNegativeResultGoldenTests
{
    [TestMethod]
    public void Session_failure_boundary_returns_the_existing_envelope_with_safe_next_action()
    {
        OperationResult result = SessionFailureBoundary.Execute(PublicCommand.SessionVerify, static () => throw new InvalidOperationException("secret token=unsafe stack trace"));
        JsonObject document = Orbyss.ProgramKit.Kernel.Operations.OperationResultProjector.ToJson(result);
        Assert.AreEqual("program-kit.operation-result/v1", document["schema"]!.GetValue<string>());
        Assert.AreEqual("program-kit.kernel/PKINT0001", document["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.AreEqual("stop", document["primaryDisposition"]!.GetValue<string>());
        Assert.IsFalse(document.ToJsonString().Contains("unsafe", StringComparison.OrdinalIgnoreCase));
    }

    [TestMethod]
    public void Every_reserved_session_diagnostic_projects_a_valid_safe_result()
    {
        List<string> goldenDocuments = new();
        foreach (KeyValuePair<string, SessionDiagnosticDefinition> item in SessionDiagnosticCatalog.Entries)
        {
            Orbyss.ProgramKit.Contracts.Diagnostics.Diagnostic diagnostic = SessionDiagnosticFactory.Create(
                item.Key,
                OperationPhase.Validation,
                "session-integration",
                "Observed bounded contract failure.");
            OperationResult result = Orbyss.ProgramKit.Kernel.Operations.OperationResultFactory.Failure(
                PublicCommand.SessionVerify,
                item.Value.Severity == "warning" ? OperationOutcome.NeedsInput : OperationOutcome.Blocked,
                OperationPhase.Validation,
                EffectState.None,
                ParseDisposition(item.Value.Disposition),
                new[] { diagnostic });
            JsonObject document = Orbyss.ProgramKit.Kernel.Operations.OperationResultProjector.ToJson(result);
            Assert.AreEqual(item.Key, document["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
            Assert.IsFalse(document.ToJsonString().Contains("password", StringComparison.OrdinalIgnoreCase));
            goldenDocuments.Add(document.ToJsonString());
        }
        Assert.AreEqual("sha256:6c72c60b19a44e2ef7ef2279eac0a269576c5ff9f38f349d25142189a4dc5947", Orbyss.ProgramKit.Kernel.Canonicalization.Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', goldenDocuments))));
    }

    private static PrimaryDisposition ParseDisposition(string value) => value switch
    {
        "retry" => PrimaryDisposition.Retry,
        "provide-input" => PrimaryDisposition.ProvideInput,
        "repair" => PrimaryDisposition.Repair,
        "revise" => PrimaryDisposition.Revise,
        _ => PrimaryDisposition.Stop,
    };
}
