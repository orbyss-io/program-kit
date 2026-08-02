using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Providers.Codex.Diagnostics;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionNegativeResultGoldenTests
{
    [TestMethod]
    public void Session_failure_boundary_returns_the_existing_envelope_with_safe_next_action()
    {
        OperationResult result = SessionFailureBoundary.Execute(PublicCommand.SessionVerify, static () => throw new InvalidOperationException("secret token=unsafe stack trace"));
        JsonObject document = Orbyss.ProgramKit.Kernel.Operations.OperationResultProjector.ToJson(result);
        ContractAssertions.AssertValid(ContractAssertions.OperationResult, document);
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
                OperationOutcome.Blocked,
                OperationPhase.Validation,
                EffectState.None,
                item.Value.Disposition,
                new[] { diagnostic });
            JsonObject document = Orbyss.ProgramKit.Kernel.Operations.OperationResultProjector.ToJson(result);
            ContractAssertions.AssertValid(ContractAssertions.OperationResult, document);
            Assert.AreEqual(item.Key, document["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
            Assert.IsFalse(document.ToJsonString().Contains("password", StringComparison.OrdinalIgnoreCase));
            goldenDocuments.Add(document.ToJsonString());
        }
        foreach (KeyValuePair<string, SessionDiagnosticDefinition> item in CodexDiagnosticCatalog.Entries)
        {
            Orbyss.ProgramKit.Contracts.Diagnostics.Diagnostic diagnostic = CodexDiagnosticFactory.Create(
                item.Key,
                OperationPhase.Validation,
                "codex-session-integration",
                "Observed bounded provider contract failure.");
            OperationResult result = Orbyss.ProgramKit.Kernel.Operations.OperationResultFactory.Failure(
                PublicCommand.SessionVerify,
                OperationOutcome.Blocked,
                OperationPhase.Validation,
                EffectState.None,
                item.Value.Disposition,
                new[] { diagnostic });
            JsonObject document = Orbyss.ProgramKit.Kernel.Operations.OperationResultProjector.ToJson(result);
            ContractAssertions.AssertValid(ContractAssertions.OperationResult, document);
            Assert.AreEqual(item.Key, document["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
            goldenDocuments.Add(document.ToJsonString());
        }
        Assert.AreEqual("sha256:f57590685ce39389c0d5d5440bdfbd78a19442627629b4cac1637c966a4ad3da", Orbyss.ProgramKit.Kernel.Canonicalization.Digests.Sha256(Encoding.UTF8.GetBytes(string.Join('\n', goldenDocuments))));
    }
}
