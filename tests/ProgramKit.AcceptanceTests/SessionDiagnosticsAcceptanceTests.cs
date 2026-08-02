using System.IO;
using System.Text.Json.Nodes;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionDiagnosticsAcceptanceTests
{
    [TestMethod]
    public void Source_authoring_workspace_is_refused_with_the_stable_session_diagnostic()
    {
        string marker = Path.Combine(TestRepository.Root, ".program-kit-source.json");
        (int exitCode, string output, _) = TestRepository.RunCli("session", "explain", "--workspace", TestRepository.Root, "--request", marker, "--format", "json");
        Assert.AreEqual(3, exitCode, output);
        JsonNode result = JsonNode.Parse(output) ?? throw new InvalidDataException("Expected a JSON result.");
        Assert.AreEqual("program-kit.session/PKSES0006", result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.AreEqual("stop", result["primaryDisposition"]!.GetValue<string>());
    }

    [TestMethod]
    public void Cli_release_mismatch_is_refused_without_an_effect()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        string request = SessionIntegrationFixture.ExplainRequest(workspace.Root);
        JsonObject document = JsonNode.Parse(File.ReadAllText(request))!.AsObject();
        document["cliRelease"]!["packageVersion"] = "0.0.0-unreviewed";
        File.WriteAllText(request, document.ToJsonString());

        (int exitCode, string output, _) = TestRepository.RunCli("session", "explain", "--workspace", workspace.Root, "--request", request, "--format", "json");
        Assert.AreEqual(3, exitCode, output);
        JsonNode result = JsonNode.Parse(output) ?? throw new InvalidDataException("Expected a JSON result.");
        Assert.AreEqual("program-kit.session/PKSES0001", result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.AreEqual("none", result["effectState"]!.GetValue<string>());
    }

    [TestMethod]
    public void Drifted_admitted_projection_reports_repair_without_mutation()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        Assert.AreEqual(0, TestRepository.RunCli("session", "install", "--workspace", workspace.Root, "--request", requests.Install, "--format", "json").ExitCode);
        string skill = Path.Combine(workspace.Root, ".agents", "skills", "program-kit", "SKILL.md");
        File.AppendAllText(skill, "\nconsumer drift");
        string before = TestRepository.DigestTree(workspace.Root);

        (int exitCode, string output, _) = TestRepository.RunCli("session", "verify", "--workspace", workspace.Root, "--request", requests.Verify, "--format", "json");
        Assert.AreEqual(3, exitCode, output);
        JsonNode result = JsonNode.Parse(output) ?? throw new InvalidDataException("Expected a JSON result.");
        Assert.AreEqual("program-kit.session/PKSES0004", result["diagnostics"]!["items"]![0]!["id"]!.GetValue<string>());
        Assert.AreEqual("repair", result["primaryDisposition"]!.GetValue<string>());
        Assert.AreEqual(before, TestRepository.DigestTree(workspace.Root));
    }
}
