namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal sealed class TestTaskMiddlewareTracker
{
    internal int SelectedInvocations { get; set; }

    internal int UnselectedInvocations { get; set; }
}
