using System;
using System.Threading.Tasks;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;

namespace Orbyss.ProgramKit.Kernel.Operations;

public static class ProviderInvocation
{
    public static T Invoke<T>(Func<Task<T>> invocation, OperationPhase phase)
    {
        try
        {
            return invocation().GetAwaiter().GetResult();
        }
        catch (ProgramKitDiagnosticException)
        {
            throw;
        }
        catch (Exception exception) when (exception is not OperationCanceledException)
        {
            throw new ProgramKitDiagnosticException(
                DiagnosticIds.ExternalFailure,
                phase,
                PrimaryDisposition.Retry,
                "The selected provider failed before returning a valid bounded observation.");
        }
    }
}
