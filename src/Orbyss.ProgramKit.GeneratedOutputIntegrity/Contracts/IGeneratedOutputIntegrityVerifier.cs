namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Verifies one generated root against its manifest and external anchor.</summary>
public interface IGeneratedOutputIntegrityVerifier
{
    /// <summary>Recomputes current bytes and reports every observable drift item.</summary>
    ValueTask<GeneratedOutputIntegrityResult> VerifyAsync(
        string rootPath,
        CancellationToken cancellationToken);
}
