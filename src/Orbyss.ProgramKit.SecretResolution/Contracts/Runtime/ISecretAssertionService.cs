namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Provider-owned service that creates bounded assertions.</summary>
public interface ISecretAssertionService
{
    /// <summary>Creates one assertion without storing it in canonical configuration.</summary>
    ValueTask<ISecretAssertionLease> CreateAsync(CancellationToken cancellationToken);
}
