namespace Orbyss.ProgramKit.Serialization.Json.Metadata;

/// <summary>Creates stable assembly-name-qualified type claims without assembly versions.</summary>
internal static class JsonTargetTypeIdentity
{
    internal static string For<T>() => For(typeof(T));

    internal static string For(Type type)
    {
        ArgumentNullException.ThrowIfNull(type);
        if (type.IsByRef || type.IsPointer)
        {
            throw new ArgumentException(
                "By-reference and pointer types cannot be stable JSON target claims.",
                nameof(type));
        }

        if (type.IsArray)
        {
            if (type.GetArrayRank() == 1 && !type.IsSZArray)
            {
                throw new ArgumentException(
                    "Non-SZ rank-one arrays are not supported JSON target claims.",
                    nameof(type));
            }

            var elementType = type.GetElementType()
                ?? throw new ArgumentException(
                    "An array target must expose its element type.",
                    nameof(type));
            var rank = type.GetArrayRank();
            return string.Concat(
                For(elementType),
                rank == 1 ? "[]" : string.Concat("[", new string(',', rank - 1), "]"));
        }

        if (type.IsGenericParameter)
        {
            return string.Concat("!", type.GenericParameterPosition);
        }

        var fullName = type.FullName
            ?? throw new ArgumentException(
                "A JSON target type must have a stable full name.",
                nameof(type));
        var assemblyName = type.Assembly.GetName().Name
            ?? throw new ArgumentException(
                "A JSON target type must have a stable assembly name.",
                nameof(type));

        if (type.IsGenericType && !type.IsGenericTypeDefinition)
        {
            var definition = type.GetGenericTypeDefinition();
            if (definition.IsNested)
            {
                throw new ArgumentException(
                    "Nested constructed generic types are not supported JSON target claims.",
                    nameof(type));
            }

            var definitionName = definition.FullName
                ?? throw new ArgumentException(
                    "A generic JSON target type must have a stable definition name.",
                    nameof(type));
            var tickIndex = definitionName.IndexOf('`');
            if (tickIndex >= 0)
            {
                definitionName = definitionName[..tickIndex];
            }

            var arguments = type
                .GetGenericArguments()
                .Select(For);
            return string.Concat(
                definitionName,
                "<",
                string.Join(",", arguments),
                ">, ",
                assemblyName);
        }

        return string.Concat(fullName, ", ", assemblyName);
    }
}
