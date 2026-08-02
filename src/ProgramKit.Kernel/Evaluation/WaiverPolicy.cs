using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;

namespace Orbyss.ProgramKit.Kernel.Evaluation;

public static class WaiverPolicy
{
    public static void EnsureFirstSliceContainsNoWaivers(JsonArray waivers)
    {
        if (waivers.Count > 0)
        {
            throw new ProgramKitDiagnosticException(
                DiagnosticIds.InvalidWaiver,
                OperationPhase.Evaluation,
                PrimaryDisposition.Stop,
                "The first vertical slice has no waivable gate; the supplied waiver is invalid.");
        }
    }
}
