using Orbyss.ProgramKit.Contracts.SessionIntegration;

namespace Orbyss.ProgramKit.SessionIntegration.Providers.ClaudeCode.Conformance;

public enum CanonicalDependencyStatus
{
    Accepted,
    Rejected,
    Missing,
    Stale,
    Mismatched,
}

public sealed record ClaudeSupportDecision(
    SessionProviderSupport SupportClaim,
    bool ReleaseEligible,
    string Limitation);

public static class ClaudeSupportAdmissionEvaluator
{
    public static ClaudeSupportDecision Evaluate(
        CanonicalDependencyStatus dependency,
        bool deterministicGatesPassed,
        bool providerCompatible)
    {
        if (dependency != CanonicalDependencyStatus.Accepted)
            return new(SessionProviderSupport.NotEvaluated, false, "canonical-dependency-not-accepted");
        if (!deterministicGatesPassed)
            return new(SessionProviderSupport.NotEvaluated, false, "deterministic-gates-incomplete");
        if (!providerCompatible)
            return new(SessionProviderSupport.Incompatible, false, "provider-surface-incompatible");
        return new(SessionProviderSupport.Supported, true, "none");
    }
}
