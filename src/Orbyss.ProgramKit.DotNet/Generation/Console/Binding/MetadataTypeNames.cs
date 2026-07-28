using System.Reflection.Metadata;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

internal static class MetadataTypeNames
{
    internal static string Definition(
        MetadataReader metadata,
        TypeDefinitionHandle handle)
    {
        var definition = metadata.GetTypeDefinition(handle);
        var name = metadata.GetString(definition.Name);
        var declaring = definition.GetDeclaringType();
        return declaring.IsNil
            ? Qualify(metadata.GetString(definition.Namespace), name)
            : string.Concat(Definition(metadata, declaring), "+", name);
    }

    internal static string Reference(
        MetadataReader metadata,
        TypeReferenceHandle handle)
    {
        var reference = metadata.GetTypeReference(handle);
        var name = metadata.GetString(reference.Name);
        return reference.ResolutionScope.Kind == HandleKind.TypeReference
            ? string.Concat(
                Reference(
                    metadata,
                    (TypeReferenceHandle)reference.ResolutionScope),
                "+",
                name)
            : Qualify(metadata.GetString(reference.Namespace), name);
    }

    internal static string Entity(
        MetadataReader metadata,
        EntityHandle handle) =>
        handle.Kind switch
        {
            HandleKind.TypeDefinition =>
                Definition(metadata, (TypeDefinitionHandle)handle),
            HandleKind.TypeReference =>
                Reference(metadata, (TypeReferenceHandle)handle),
            _ => string.Empty,
        };

    private static string Qualify(string namespaceName, string name) =>
        string.IsNullOrEmpty(namespaceName)
            ? name
            : string.Concat(namespaceName, ".", name);
}
