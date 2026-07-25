using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Generates runtime-only bounded secret lifecycle subscriptions.</summary>
public interface IDotNetSecretSubscriptionCompiler
{
    /// <summary>Compiles a subscription and its consumer-owned reaction boundary.</summary>
    ImmutableArray<GeneratedOutput> Compile(DotNetSecretSubscriptionDefinition definition);

    /// <summary>Renders the exact generated hosted-service registration.</summary>
    string RenderRegistration(DotNetSecretSubscriptionDefinition definition);
}
