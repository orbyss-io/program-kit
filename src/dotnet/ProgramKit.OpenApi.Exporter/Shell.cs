using System.Text.Json;

namespace ProgramKit.OpenApiExport;

/// <summary>Captures the activated feature set and effective HTTP prefix of one configured shell.</summary>
internal sealed record Shell(string[] Features, string RoutePrefix)
{
    /// <summary>Reads one shell without activating it or executing its lifecycle initializers.</summary>
    public static Shell Read(JsonElement root, string name)
    {
        if (!root.GetProperty("CShells").GetProperty("Shells").TryGetProperty(name, out var shell))
            throw new InvalidOperationException($"configured shell '{name}' does not exist.");
        var features = shell.GetProperty("Features").EnumerateObject().Select(item => item.Name).ToArray();
        var routing = shell.TryGetProperty("Configuration", out var configuration) &&
                      configuration.TryGetProperty("WebRouting", out var webRouting)
            ? webRouting
            : default;
        var segments = new[] { Property(routing, "Path"), Property(routing, "RoutePrefix") }
            .Where(value => !string.IsNullOrWhiteSpace(value))
            .Select(value => value!.Trim('/'));
        var route = string.Join('/', segments);
        return new Shell(features, route.Length == 0 ? "" : "/" + route);
    }

    /// <summary>Reads an optional string property from a routing object.</summary>
    private static string? Property(JsonElement element, string name) =>
        element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out var value)
            ? value.GetString()
            : null;
}
