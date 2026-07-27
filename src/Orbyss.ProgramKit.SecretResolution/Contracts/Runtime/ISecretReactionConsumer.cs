using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Consumer-owned implementation of one declared lifecycle reaction.</summary>
public interface ISecretReactionConsumer
{
    /// <summary>Applies the declared reaction and reports its material-free result.</summary>
    ValueTask<SecretReactionResult> ApplyAsync(
        SecretReactionRequest request,
        CancellationToken cancellationToken);
}
