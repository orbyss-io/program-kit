using System;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Intake;

namespace Orbyss.ProgramKit.Kernel.Authority;

public sealed class RepositoryAuthorityProvider
{
    public void Demand(FactoryInput input)
    {
        if (input.RequestedEffect == RequestedEffect.None)
        {
            return;
        }

        if (!input.AuthorityApproved)
        {
            throw new UnauthorizedAccessException("No exact repository authority record approves the requested effect.");
        }

        if (input.EvaluationInstant < input.AuthorityNotBefore || input.EvaluationInstant > input.AuthorityNotAfter)
        {
            throw new UnauthorizedAccessException("The exact authority record is not valid at the approved evaluation instant.");
        }
    }
}
