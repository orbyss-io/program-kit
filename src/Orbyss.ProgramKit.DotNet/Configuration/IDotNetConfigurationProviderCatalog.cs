namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Explicit provider descriptor registry with no ambient discovery.</summary>
public interface IDotNetConfigurationProviderCatalog
{
    /// <summary>All exact provider revisions registered for this generation session.</summary>
    ImmutableArray<DotNetConfigurationProviderDescriptor> Providers { get; }

    /// <summary>Resolves one exact provider revision or returns <see langword="null"/>.</summary>
    DotNetConfigurationProviderDescriptor? Resolve(ArtifactReference providerRevision);
}
