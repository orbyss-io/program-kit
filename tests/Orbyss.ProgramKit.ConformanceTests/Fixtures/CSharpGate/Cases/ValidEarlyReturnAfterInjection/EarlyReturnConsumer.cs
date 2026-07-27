namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidEarlyReturnAfterInjection;

internal sealed class EarlyReturnConsumer
{
    private readonly IEarlyReturnHandler handler;

    internal EarlyReturnConsumer(
        IEarlyReturnHandler handler,
        bool returnImmediately)
    {
        this.handler = handler;
        if (returnImmediately)
        {
            return;
        }
    }

    internal void Handle() => handler.Handle();
}
