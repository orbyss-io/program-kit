using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Consumer-owned sink for validated reaction outcomes.</summary>
public interface ISecretReactionOutcomeSink
{
    /// <summary>Records a material-free outcome; it is not a security or business ledger.</summary>
    void Report(SecretReactionResult result);
}
