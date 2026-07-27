namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Explicit transport authorization disposition for one operation route.</summary>
public enum DotNetOperationSecurityDisposition
{
    /// <summary>The operation route is explicitly anonymous.</summary>
    Anonymous,

    /// <summary>The operation route requires one named host policy.</summary>
    NamedPolicy,
}
