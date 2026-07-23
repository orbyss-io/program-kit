namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.NovelBehaviorConstruction;

internal static class ConstructionProbe
{
    internal static IWorkflowOperations Create()
    {
        IWorkflowOperations operations = new WorkflowOperations();
        return operations;
    }
}
