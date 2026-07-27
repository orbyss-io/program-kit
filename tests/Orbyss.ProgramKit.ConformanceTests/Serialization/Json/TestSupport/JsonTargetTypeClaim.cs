namespace Orbyss.ProgramKit.ConformanceTests.Serialization.Json.TestSupport;

internal static class JsonTargetTypeClaim
{
    internal static string For<T>() => For(typeof(T));

    internal static string For(Type type)
    {
        ArgumentNullException.ThrowIfNull(type);

        if (type.IsArray)
        {
            var elementType = type.GetElementType()
                ?? throw new ArgumentException(
                    "The test target array must expose its element type.",
                    nameof(type));
            var rank = type.GetArrayRank();
            return string.Concat(
                For(elementType),
                rank == 1 ? "[]" : string.Concat("[", new string(',', rank - 1), "]"));
        }

        var fullName = type.FullName
            ?? throw new ArgumentException(
                "The test target must have a stable full name.",
                nameof(type));
        var assemblyName = type.Assembly.GetName().Name
            ?? throw new ArgumentException(
                "The test target must have a stable assembly name.",
                nameof(type));

        if (!type.IsGenericType || type.IsGenericTypeDefinition)
        {
            return string.Concat(fullName, ", ", assemblyName);
        }

        var definitionName = type.GetGenericTypeDefinition().FullName
            ?? throw new ArgumentException(
                "The test generic target must have a stable definition name.",
                nameof(type));
        var tickIndex = definitionName.IndexOf('`');
        if (tickIndex >= 0)
        {
            definitionName = definitionName[..tickIndex];
        }

        return string.Concat(
            definitionName,
            "<",
            string.Join(",", type.GetGenericArguments().Select(For)),
            ">, ",
            assemblyName);
    }
}
