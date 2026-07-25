namespace Orbyss.ProgramKit.SecretResolution.Contracts.Runtime;

/// <summary>Opaque mounted-file capability that avoids exposing a canonical path string.</summary>
public interface ISecretMountedFileHandle
{
    /// <summary>Opens the provider- or orchestrator-owned mounted content.</summary>
    Stream OpenRead();
}
