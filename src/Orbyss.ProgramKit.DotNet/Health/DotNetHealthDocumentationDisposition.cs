namespace Orbyss.ProgramKit.DotNet.Health;

/// <summary>Whether health is excluded or projected through an owned operation.</summary>
public enum DotNetHealthDocumentationDisposition
{
    /// <summary>Health is excluded from integrator documentation.</summary>
    Excluded,

    /// <summary>Health is documented through an exact owned operation.</summary>
    OwnedOperation,
}
