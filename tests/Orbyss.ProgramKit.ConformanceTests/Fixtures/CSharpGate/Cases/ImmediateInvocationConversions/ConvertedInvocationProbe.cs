namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationConversions;

public sealed class ConvertedInvocationProbe
{
    public void Run()
    {
        ((IInvocationTarget)new InvocationRecord()).Run();
        (new InvocationRecord() as IInvocationTarget)!.Run();
        (true ? new InvocationRecord() : new InvocationRecord()).Run();
        (new InvocationRecord() with { }).Run();
    }
}
