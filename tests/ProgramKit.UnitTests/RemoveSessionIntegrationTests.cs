using System;
using System.IO;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Publication;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class RemoveSessionIntegrationTests
{
    [TestMethod]
    public void Absent_installation_is_not_inferred_or_deleted()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        workspace.Write("consumer.txt", Encoding.UTF8.GetBytes("preserve"));
        string request = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);
        OperationResult result = new RemoveSessionIntegrationOperation(SessionIntegrationFixture.Services()).Execute(workspace.Root, request);
        Assert.AreEqual(OperationOutcome.Blocked, result.Outcome);
        Assert.AreEqual("program-kit.session/PKSES0008", result.Diagnostics.Items[0].Id);
        Assert.AreEqual("preserve", File.ReadAllText(workspace.PathOf("consumer.txt")));
    }

    [TestMethod]
    public void Exact_installation_is_removed_and_already_removed_is_idempotent()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        Install(workspace);
        workspace.Write("consumer.txt", Encoding.UTF8.GetBytes("preserve"));
        string request = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);
        OperationResult removed = new RemoveSessionIntegrationOperation(SessionIntegrationFixture.Services()).Execute(workspace.Root, request);
        Assert.AreEqual(OperationOutcome.Succeeded, removed.Outcome);
        Assert.AreEqual(EffectState.Committed, removed.EffectState);
        Assert.IsFalse(File.Exists(workspace.PathOf(".agents/skills/program-kit/SKILL.md")));
        OperationResult verified = new VerifySessionIntegrationOperation(SessionIntegrationFixture.Services()).Execute(workspace.Root, SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root).Verify);
        Assert.AreEqual(OperationOutcome.Succeeded, verified.Outcome);
        Assert.AreEqual("removed", verified.Session!["state"]!.GetValue<string>());
        Assert.AreEqual("preserve", File.ReadAllText(workspace.PathOf("consumer.txt")));
        Assert.AreEqual(SessionIntegrationState.Removed, new SessionInstallationStore(workspace.Root, "codex").Inspect().State);

        string secondRequest = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);
        OperationResult repeated = new RemoveSessionIntegrationOperation(SessionIntegrationFixture.Services()).Execute(workspace.Root, secondRequest);
        Assert.AreEqual(OperationOutcome.Succeeded, repeated.Outcome);
        Assert.AreEqual(EffectState.None, repeated.EffectState);
    }

    [TestMethod]
    [DataRow("drift")]
    [DataRow("missing")]
    public void Drifted_or_partial_installation_refuses_every_removal(string state)
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        Install(workspace);
        string skill = workspace.PathOf(".agents/skills/program-kit/SKILL.md");
        if (state == "drift") File.AppendAllText(skill, "\nconsumer change"); else File.Delete(skill);
        string request = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);
        string before = TestRepository.DigestTree(workspace.Root);
        OperationResult result = new RemoveSessionIntegrationOperation(SessionIntegrationFixture.Services()).Execute(workspace.Root, request);
        Assert.AreEqual(OperationOutcome.Blocked, result.Outcome);
        Assert.AreEqual(before, TestRepository.DigestTree(workspace.Root));
    }

    [TestMethod]
    public void Interrupted_removal_rolls_back_owned_bytes_and_record()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        Install(workspace);
        string request = SessionIntegrationFixture.WriteRemoveRequest(workspace.Root);
        byte[] before = File.ReadAllBytes(workspace.PathOf(".agents/skills/program-kit/SKILL.md"));
        RemoveSessionIntegrationOperation operation = new(SessionIntegrationFixture.Services(), new SessionRemovalJournal(new ThrowAfterFirstRemoval()));
        OperationResult interrupted = operation.Execute(workspace.Root, request);
        Assert.AreEqual(OperationOutcome.Blocked, interrupted.Outcome);
        Assert.AreEqual(EffectState.Indeterminate, interrupted.EffectState);
        Assert.AreEqual("program-kit.session/PKSES0005", interrupted.Diagnostics.Items[0].Id);
        CollectionAssert.AreEqual(before, File.ReadAllBytes(workspace.PathOf(".agents/skills/program-kit/SKILL.md")));
        Assert.AreEqual(SessionIntegrationState.Exact, new SessionInstallationStore(workspace.Root, "codex").Inspect().State);
        Assert.IsFalse(File.Exists(workspace.PathOf(".program-kit/workspace.lock")));
    }

    private static void Install(SessionIntegrationTestWorkspace workspace)
    {
        SessionRequestPaths requests = SessionIntegrationFixture.WriteLifecycleRequests(workspace.Root);
        OperationResult result = new InstallSessionIntegrationOperation(SessionIntegrationFixture.Services()).Execute(workspace.Root, requests.Install);
        Assert.AreEqual(OperationOutcome.Succeeded, result.Outcome);
    }

    private sealed class ThrowAfterFirstRemoval : ISessionRemovalObserver
    {
        public void Removed(int completedCount, string logicalPath) => throw new InvalidOperationException("Injected interruption.");
    }
}
