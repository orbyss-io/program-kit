namespace PublishedTools.Contract.Api;

/// <summary>Test sentinel proving metadata composition cannot construct storage.</summary>
public sealed class UnstartedDataSource
{
    /// <summary>Always fails if the exporter resolves operation storage.</summary>
    public UnstartedDataSource() => throw new InvalidOperationException("PUBLISHED_TOOL_STORAGE_CONSTRUCTED");
}
