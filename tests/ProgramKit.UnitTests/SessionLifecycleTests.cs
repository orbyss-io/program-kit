using System.IO;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Publication;

namespace Orbyss.ProgramKit.Tests;

[TestClass]
public sealed class SessionLifecycleTests
{
    [TestMethod]
    public void Store_distinguishes_absent_exact_drifted_and_reload_state_without_mutating()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        SessionInstallationStore store = new(workspace.Root, "codex");
        Assert.AreEqual(SessionIntegrationState.Absent, store.Inspect().State);

        byte[] skill = Encoding.UTF8.GetBytes("skill");
        workspace.Write(".agents/skills/program-kit/SKILL.md", skill);
        store.Admit(SessionIntegrationFixture.InstallationRecord(workspace.Root, skill));
        SessionInstallationInspection exact = store.Inspect();
        Assert.AreEqual(SessionIntegrationState.Exact, exact.State);
        Assert.AreEqual(SessionAvailability.ReloadRequired, exact.SessionAvailability);

        File.WriteAllText(workspace.PathOf(".agents/skills/program-kit/SKILL.md"), "drift");
        Assert.AreEqual(SessionIntegrationState.Drifted, store.Inspect().State);
    }

    [TestMethod]
    public void Source_authoring_workspace_is_never_adopted_as_a_consumer()
    {
        using SessionIntegrationTestWorkspace workspace = SessionIntegrationTestWorkspace.Create();
        workspace.Write(".program-kit-source.json", Encoding.UTF8.GetBytes("{}"));
        SessionDiagnosticException exception = Assert.ThrowsExactly<SessionDiagnosticException>(() => new ExplainSessionIntegrationOperation(SessionIntegrationFixture.Services()).Execute(workspace.Root, SessionIntegrationFixture.ExplainRequest(workspace.Root)));
        Assert.AreEqual(SessionDiagnosticCatalog.Id(6), exception.DiagnosticId);
    }
}
