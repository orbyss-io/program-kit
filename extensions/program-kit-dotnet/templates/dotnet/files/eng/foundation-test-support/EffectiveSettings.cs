using System.Collections;
using System.Reflection;
using System.Text.Json;
using Microsoft.Extensions.Configuration;

namespace ProgramKit.Foundation.TestSupport;

/// <summary>Read-only test/operations capture of already activated typed options.
/// It resolves no options, changes no configuration, and exposes no HTTP endpoint.</summary>
public static class EffectiveSettings
{
    /// <summary>Observe actual typed values and the last native provider for each declared key.
    /// The caller passes the options instance used by the activated feature, never a freshly bound copy.</summary>
    public static IReadOnlyList<SettingObservation> Capture<T>(IConfigurationRoot configuration,
        T activatedOptions, string sectionName, IEnumerable<JsonElement> settings,
        IReadOnlyDictionary<int, string>? providerNames = null) where T : notnull
    {
        ArgumentNullException.ThrowIfNull(configuration);
        ArgumentNullException.ThrowIfNull(activatedOptions);
        var observations = new List<SettingObservation>();
        var paths = new HashSet<string>(StringComparer.Ordinal);
        var providers = configuration.Providers.ToArray();
        foreach (var setting in settings)
        {
            var path = setting.GetProperty("path").GetString()!;
            if (!path.StartsWith(sectionName + ":", StringComparison.Ordinal)) continue;
            if (!paths.Add(path)) throw new InvalidOperationException("Duplicate runtime setting metadata path: " + path);
            if (path.Contains('{', StringComparison.Ordinal))
                throw new InvalidOperationException("Instantiate named configuration paths before runtime observation.");
            var secret = setting.GetProperty("secret").GetBoolean();
            // Secret getters and configured values are deliberately never read.
            object? value = secret ? "<redacted>" : ReadProperty(activatedOptions, path[(sectionName.Length + 1)..]);
            var section = configuration.GetSection(path);
            var keys = LeafKeys(section).DefaultIfEmpty(path).ToArray();
            var sources = new List<SettingSource>();
            foreach (var key in keys)
            {
                var index = Array.FindLastIndex(providers, provider => provider.TryGet(key, out _));
                var name = index < 0 ? "typed default or options delegate" :
                    providerNames is not null && providerNames.TryGetValue(index, out var declared) ? declared :
                    providers[index].GetType().FullName!;
                sources.Add(new(key, index < 0 ? null : index, name));
            }
            observations.Add(new(path, value, activatedOptions.GetType().FullName!,
                setting.GetProperty("binding").GetString()!, setting.GetProperty("reload").GetString()!,
                setting.GetProperty("constraints").Clone(), sources,
                "Activated typed value; provider provenance describes configured inputs. Options delegates/normalization can change that value."));
        }
        if (observations.Count == 0) throw new InvalidOperationException("Selected options metadata produced no runtime observations.");
        return observations;
    }

    /// <summary>Reads the declared public options property without rebinding a configuration copy.</summary>
    private static object? ReadProperty(object value, string relative)
    {
        object? current = value;
        foreach (var part in relative.Split(':'))
        {
            if (current is IDictionary dictionary)
            {
                if (!dictionary.Contains(part)) throw new InvalidOperationException("Named bound setting is absent: " + relative);
                current = dictionary[part];
            }
            else
            {
                var property = current?.GetType().GetProperty(part, BindingFlags.Public | BindingFlags.Instance);
                if (property is null || property.GetIndexParameters().Length != 0)
                    throw new InvalidOperationException("Declared setting has no actual bound property: " + relative);
                current = property.GetValue(current);
            }
        }
        return current;
    }

    /// <summary>Enumerates scalar and collection configuration inputs for native provider provenance.</summary>
    private static IEnumerable<string> LeafKeys(IConfigurationSection section)
    {
        var children = section.GetChildren().ToArray();
        if (children.Length == 0)
        {
            if (section.Value is not null) yield return section.Path;
        }
        else
            foreach (var child in children)
                foreach (var key in LeafKeys(child)) yield return key;
    }
}
