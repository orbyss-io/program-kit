namespace ProgramKit.Examples.PostgreSql;

/// <summary>Stores one synthetic operation through the provider-private EF model.</summary>
public sealed class NativeMigrationEntry
{
    /// <summary>Gets or sets the generated row identity.</summary>
    public long Id { get; set; }

    /// <summary>Gets or sets the unique synthetic operation value.</summary>
    public string Value { get; set; } = string.Empty;
}
