using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation;

/// <summary>Design-time input for one generated bounded secret-change subscription.</summary>
public sealed record DotNetSecretSubscriptionDefinition(
    SecretResolutionContract Contract,
    string Namespace,
    string TypeName,
    int QueueCapacity);
