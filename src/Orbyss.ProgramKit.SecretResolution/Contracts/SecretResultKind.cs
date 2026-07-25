namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Finite capability shapes a resolver may return.</summary>
public enum SecretResultKind
{
    /// <summary>No result capability was selected.</summary>
    Unspecified,
    /// <summary>Configuration-shaped character material.</summary>
    ConfigurationText,
    /// <summary>Configuration-shaped byte material.</summary>
    ConfigurationBytes,
    /// <summary>A certificate capability.</summary>
    Certificate,
    /// <summary>A handle that opens provider- or orchestrator-owned mounted material.</summary>
    MountedFileHandle,
    /// <summary>An opaque provider credential object or handle.</summary>
    CredentialHandle,
    /// <summary>A service that produces bounded assertions.</summary>
    AssertionService,
    /// <summary>A workload or managed-identity capability with no returned secret material.</summary>
    WorkloadIdentityCapability,
}
