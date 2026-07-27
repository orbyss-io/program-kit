namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Maximum secret-bearing responsibility assigned to a source.</summary>
public enum DotNetConfigurationSecretClassification
{
    /// <summary>The source may contain only non-secret material.</summary>
    PublicOnly,
    /// <summary>The source may contain opaque references, never resolved secret material.</summary>
    ReferencesOnly,
    /// <summary>The provider owns secret material outside Program Kit projections.</summary>
    ProviderOwned,
}
