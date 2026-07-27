namespace Orbyss.ProgramKit.DotNet.Health;

/// <summary>Reviewed listener exposure category.</summary>
public enum DotNetHealthExposure
{
    /// <summary>Loopback-only management listener.</summary>
    Loopback,

    /// <summary>Private-network listener with explicit transport policy.</summary>
    PrivateNetwork,

    /// <summary>Public listener with explicit transport and authority policy.</summary>
    Public,
}
