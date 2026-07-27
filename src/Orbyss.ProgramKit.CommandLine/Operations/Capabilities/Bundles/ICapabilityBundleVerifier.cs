namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

/// <summary>Verifies one exact capability bundle package.</summary>
public interface ICapabilityBundleVerifier
{
    /// <summary>Verifies a supplied bundle and every allow-listed payload byte.</summary>
    ValueTask VerifyAsync(
        string bundlePath,
        CancellationToken cancellationToken);
}
