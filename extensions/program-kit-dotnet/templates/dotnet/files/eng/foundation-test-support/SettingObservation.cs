using System.Text.Json;

namespace ProgramKit.Foundation.TestSupport;

/// <summary>A declared setting observed after native feature activation.</summary>
public sealed record SettingObservation(string Path, object? Value, string OwnerType, string Binding,
    string Reload, JsonElement Constraints, IReadOnlyList<SettingSource> Sources, string Scope);
