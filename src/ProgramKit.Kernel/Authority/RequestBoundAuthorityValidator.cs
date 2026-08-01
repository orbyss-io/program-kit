using System;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;

namespace Orbyss.ProgramKit.Kernel.Authority;

public sealed class RequestBoundAuthorityValidator
{
    public void Demand(AuthorityDemand demand, RequestBoundAuthorityGrant? grant)
    {
        if (demand.Effect == RequestedEffect.None)
        {
            if (grant is not null)
                throw new UnauthorizedAccessException("Read-only operations reject authority grants so ambient approval cannot change their meaning.");
            return;
        }

        if (grant is null)
            throw new UnauthorizedAccessException("The effect-bearing request has no exact request-bound authority grant.");
        if (!string.Equals(grant.Schema, "program-kit.request-bound-authority-grant/v1", StringComparison.Ordinal))
            throw new UnauthorizedAccessException("The authority grant schema is not supported.");
        if (grant.Revoked)
            throw new UnauthorizedAccessException("The exact authority grant has been revoked.");
        if (grant.Consumed)
            throw new UnauthorizedAccessException("The exact authority grant has already been consumed and cannot be reused.");
        if (!string.Equals(grant.WorkspaceIdentity, demand.WorkspaceIdentity, StringComparison.Ordinal))
            throw new UnauthorizedAccessException("The authority subject does not match the exact workspace.");
        if (!string.Equals(grant.Operation, demand.Operation, StringComparison.Ordinal))
            throw new UnauthorizedAccessException("The authority operation does not match the exact requested operation.");
        if (!string.Equals(grant.Effect, Effect(demand.Effect), StringComparison.Ordinal))
            throw new UnauthorizedAccessException("The authority effect does not match the requested effect.");
        if (!string.Equals(grant.RequestIdentity, demand.RequestIdentity, StringComparison.Ordinal))
            throw new UnauthorizedAccessException("The authority grant is bound to a different request core identity.");
        if (!string.Equals(grant.Provider, demand.Provider, StringComparison.Ordinal))
            throw new UnauthorizedAccessException("The authority grant is bound to a different provider selection.");
        if (!string.Equals(grant.Scope, demand.Scope, StringComparison.Ordinal))
            throw new UnauthorizedAccessException("The authority grant is bound to a different installation scope.");
        if (demand.EvaluationInstant < grant.NotBefore || demand.EvaluationInstant > grant.NotAfter)
            throw new UnauthorizedAccessException("The authority grant is not valid at the exact evaluation instant.");
    }

    private static string Effect(RequestedEffect effect) => effect switch
    {
        RequestedEffect.CandidateOnly => "candidate-only",
        RequestedEffect.Committed => "committed",
        _ => "none",
    };
}
