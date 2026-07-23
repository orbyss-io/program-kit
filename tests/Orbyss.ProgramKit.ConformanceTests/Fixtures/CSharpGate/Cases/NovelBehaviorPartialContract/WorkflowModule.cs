namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.NovelBehaviorPartialContract;

internal sealed class WorkflowModule : IWorkflowOperations
{
    private bool _hasRun;

    public bool HasRun => _hasRun;

    public void Reset()
    {
        _hasRun = false;
    }

    public void Run()
    {
        _hasRun = true;
    }
}
