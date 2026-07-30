using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;

namespace Orbyss.ProgramKit.Serialization.Json.Serialization;

/// <summary>
/// Locates one strict typed-read failure from source-generated JSON metadata.
/// </summary>
internal static class StrictJsonReadFailureLocator
{
    internal static StrictJsonReadFailure Locate(
        ReadOnlyMemory<byte> canonicalJson,
        JsonTypeInfo rootType,
        JsonException? exception)
    {
        ArgumentNullException.ThrowIfNull(rootType);
        var missing = FindMissingRequired(canonicalJson, rootType);
        if (missing is not null)
        {
            return missing;
        }

        var segments = ParsePath(exception?.Path);
        var resolved = Resolve(rootType, segments);
        return new StrictJsonReadFailure(
            Pointer(segments),
            resolved.MemberName,
            TypeName(resolved.ExpectedType),
            resolved.IsUndeclaredMember);
    }

    internal static StrictJsonReadFailure Locate(
        JsonTypeInfo rootType,
        string? diagnosticPath)
    {
        ArgumentNullException.ThrowIfNull(rootType);
        var segments = ParsePointer(diagnosticPath);
        var resolved = Resolve(rootType, segments);
        return new StrictJsonReadFailure(
            Pointer(segments),
            resolved.MemberName,
            TypeName(resolved.ExpectedType),
            resolved.IsUndeclaredMember);
    }

    private static StrictJsonReadFailure? FindMissingRequired(
        ReadOnlyMemory<byte> canonicalJson,
        JsonTypeInfo rootType)
    {
        if (canonicalJson.IsEmpty)
        {
            return null;
        }

        try
        {
            var reader = new Utf8JsonReader(canonicalJson.Span);
            if (!reader.Read())
            {
                return null;
            }

            List<StrictJsonReadPathSegment> path = [];
            return FindMissingRequired(
                ref reader,
                rootType,
                path,
                0);
        }
        catch (Exception exception)
            when (exception is JsonException or InvalidOperationException)
        {
            return null;
        }
    }

    private static StrictJsonReadFailure? FindMissingRequired(
        ref Utf8JsonReader reader,
        JsonTypeInfo typeInfo,
        List<StrictJsonReadPathSegment> path,
        int depth)
    {
        if (depth >= 128)
        {
            reader.Skip();
            return null;
        }

        if (typeInfo.Kind == JsonTypeInfoKind.Object &&
            reader.TokenType == JsonTokenType.StartObject)
        {
            HashSet<string> present = new(StringComparer.Ordinal);
            while (reader.Read() &&
                   reader.TokenType != JsonTokenType.EndObject)
            {
                if (reader.TokenType != JsonTokenType.PropertyName)
                {
                    reader.Skip();
                    continue;
                }

                var propertyName = reader.GetString() ?? string.Empty;
                _ = present.Add(propertyName);
                if (!reader.Read())
                {
                    return null;
                }

                var property = typeInfo.Properties.FirstOrDefault(candidate =>
                    string.Equals(
                        candidate.Name,
                        propertyName,
                        StringComparison.Ordinal));
                if (property is null ||
                    reader.TokenType == JsonTokenType.Null)
                {
                    reader.Skip();
                    continue;
                }

                var childType = TryGetTypeInfo(
                    typeInfo,
                    property.PropertyType);
                if (childType is null)
                {
                    reader.Skip();
                    continue;
                }

                path.Add(
                    StrictJsonReadPathSegment.Property(property.Name));
                var nested = FindMissingRequired(
                    ref reader,
                    childType,
                    path,
                    depth + 1);
                path.RemoveAt(path.Count - 1);
                if (nested is not null)
                {
                    return nested;
                }
            }

            foreach (var property in typeInfo.Properties)
            {
                if (property.IsRequired && !present.Contains(property.Name))
                {
                    var missingPath = path
                        .Append(
                            StrictJsonReadPathSegment.Property(property.Name))
                        .ToArray();
                    return new StrictJsonReadFailure(
                        Pointer(missingPath),
                        property.Name,
                        TypeName(property.PropertyType),
                        false);
                }
            }
        }
        else if (typeInfo.Kind == JsonTypeInfoKind.Enumerable &&
                 reader.TokenType == JsonTokenType.StartArray)
        {
            var elementType = ElementType(typeInfo.Type);
            var elementTypeInfo = elementType is null
                ? null
                : TryGetTypeInfo(typeInfo, elementType);
            if (elementTypeInfo is null)
            {
                reader.Skip();
                return null;
            }

            var index = 0;
            while (reader.Read() &&
                   reader.TokenType != JsonTokenType.EndArray)
            {
                path.Add(StrictJsonReadPathSegment.Index(index));
                var nested = FindMissingRequired(
                    ref reader,
                    elementTypeInfo,
                    path,
                    depth + 1);
                path.RemoveAt(path.Count - 1);
                if (nested is not null)
                {
                    return nested;
                }

                index++;
            }
        }
        else if (typeInfo.Kind == JsonTypeInfoKind.Dictionary &&
                 reader.TokenType == JsonTokenType.StartObject)
        {
            var valueType = DictionaryValueType(typeInfo.Type);
            var valueTypeInfo = valueType is null
                ? null
                : TryGetTypeInfo(typeInfo, valueType);
            if (valueTypeInfo is null)
            {
                reader.Skip();
                return null;
            }

            while (reader.Read() &&
                   reader.TokenType != JsonTokenType.EndObject)
            {
                if (reader.TokenType != JsonTokenType.PropertyName)
                {
                    reader.Skip();
                    continue;
                }

                var propertyName = reader.GetString() ?? string.Empty;
                if (!reader.Read())
                {
                    return null;
                }

                path.Add(
                    StrictJsonReadPathSegment.Property(propertyName));
                var nested = FindMissingRequired(
                    ref reader,
                    valueTypeInfo,
                    path,
                    depth + 1);
                path.RemoveAt(path.Count - 1);
                if (nested is not null)
                {
                    return nested;
                }
            }
        }
        else
        {
            reader.Skip();
        }

        return null;
    }

    private static StrictJsonResolvedFailure Resolve(
        JsonTypeInfo rootType,
        IReadOnlyList<StrictJsonReadPathSegment> segments)
    {
        var current = rootType;
        var expectedType = rootType.Type;
        var memberName = "<root>";
        foreach (var segment in segments)
        {
            if (segment.PropertyName is { } propertyName)
            {
                if (current.Kind == JsonTypeInfoKind.Dictionary)
                {
                    var valueType = DictionaryValueType(current.Type);
                    memberName = propertyName;
                    if (valueType is null)
                    {
                        return new StrictJsonResolvedFailure(
                            current.Type,
                            memberName,
                            false);
                    }

                    expectedType = valueType;
                    current = TryGetTypeInfo(current, valueType) ?? current;
                    continue;
                }

                var property = current.Kind == JsonTypeInfoKind.Object
                    ? current.Properties.FirstOrDefault(candidate =>
                        string.Equals(
                            candidate.Name,
                            propertyName,
                            StringComparison.Ordinal))
                    : null;
                memberName = propertyName;
                if (property is null)
                {
                    return new StrictJsonResolvedFailure(
                        current.Type,
                        memberName,
                        true);
                }

                expectedType = property.PropertyType;
                current = TryGetTypeInfo(current, expectedType) ?? current;
            }
            else
            {
                var elementType = ElementType(expectedType);
                if (elementType is null)
                {
                    continue;
                }

                expectedType = elementType;
                current = TryGetTypeInfo(current, elementType) ?? current;
            }
        }

        return new StrictJsonResolvedFailure(
            expectedType,
            memberName,
            false);
    }

    private static JsonTypeInfo? TryGetTypeInfo(
        JsonTypeInfo owner,
        Type type)
    {
        try
        {
            return owner.Options.GetTypeInfo(type);
        }
        catch (Exception exception) when (
            exception is InvalidOperationException or NotSupportedException)
        {
            return null;
        }
    }

    private static Type? ElementType(Type type)
    {
        if (type.IsArray)
        {
            return type.GetElementType();
        }

        if (type.IsGenericType &&
            type.GetGenericArguments() is [var single])
        {
            return single;
        }

        return null;
    }

    private static Type? DictionaryValueType(Type type) =>
        type.IsGenericType &&
        type.GetGenericArguments() is [_, var value]
            ? value
            : null;

    private static List<StrictJsonReadPathSegment> ParsePath(string? path)
    {
        if (string.IsNullOrEmpty(path) || path == "$")
        {
            return [];
        }

        List<StrictJsonReadPathSegment> segments = [];
        var index = path[0] == '$' ? 1 : 0;
        while (index < path.Length)
        {
            if (path[index] == '.')
            {
                index++;
                var start = index;
                while (index < path.Length &&
                       path[index] is not '.' and not '[')
                {
                    index++;
                }

                if (index > start)
                {
                    segments.Add(
                        StrictJsonReadPathSegment.Property(
                            path[start..index]));
                }

                continue;
            }

            if (path[index] == '[')
            {
                var close = path.IndexOf(']', index + 1);
                if (close < 0)
                {
                    return segments;
                }

                var token = path[(index + 1)..close];
                if (int.TryParse(
                        token,
                        NumberStyles.None,
                        CultureInfo.InvariantCulture,
                        out var arrayIndex))
                {
                    segments.Add(
                        StrictJsonReadPathSegment.Index(arrayIndex));
                }
                else if (token.Length >= 2 &&
                         token[0] == '\'' &&
                         token[^1] == '\'')
                {
                    segments.Add(
                        StrictJsonReadPathSegment.Property(token[1..^1]));
                }

                index = close + 1;
                continue;
            }

            index++;
        }

        return segments;
    }

    private static List<StrictJsonReadPathSegment> ParsePointer(string? path)
    {
        if (string.IsNullOrEmpty(path) || path == "/")
        {
            return [];
        }

        return path.Split(
                '/',
                StringSplitOptions.RemoveEmptyEntries)
            .Select(segment =>
            {
                var decoded = segment
                    .Replace("~1", "/", StringComparison.Ordinal)
                    .Replace("~0", "~", StringComparison.Ordinal);
                return int.TryParse(
                    decoded,
                    NumberStyles.None,
                    CultureInfo.InvariantCulture,
                    out var index)
                    ? StrictJsonReadPathSegment.Index(index)
                    : StrictJsonReadPathSegment.Property(decoded);
            })
            .ToList();
    }

    private static string Pointer(
        IEnumerable<StrictJsonReadPathSegment> segments) =>
        string.Concat(segments.Select(segment =>
            string.Concat(
                "/",
                segment.PropertyName is { } property
                    ? property
                        .Replace("~", "~0", StringComparison.Ordinal)
                        .Replace("/", "~1", StringComparison.Ordinal)
                    : segment.ArrayIndex.ToString(
                        CultureInfo.InvariantCulture))));

    private static string TypeName(Type type) =>
        type.FullName ?? type.Name;
}
