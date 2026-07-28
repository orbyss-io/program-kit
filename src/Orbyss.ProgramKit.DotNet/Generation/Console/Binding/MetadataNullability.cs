using System.Reflection.Metadata;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

internal static class MetadataNullability
{
    internal static DotNetConsoleReferenceNullability Read(
        MetadataReader metadata,
        Parameter parameter,
        MethodDefinition method,
        TypeDefinition declaringType)
    {
        var flag = NullableFlag(
            metadata,
            parameter.GetCustomAttributes(),
            "System.Runtime.CompilerServices.NullableAttribute");
        flag ??= NullableFlag(
            metadata,
            method.GetCustomAttributes(),
            "System.Runtime.CompilerServices.NullableContextAttribute");
        flag ??= NullableFlag(
            metadata,
            declaringType.GetCustomAttributes(),
            "System.Runtime.CompilerServices.NullableContextAttribute");
        return flag switch
        {
            1 => DotNetConsoleReferenceNullability.NotNull,
            2 => DotNetConsoleReferenceNullability.Nullable,
            _ => DotNetConsoleReferenceNullability.NotApplicable,
        };
    }

    private static byte? NullableFlag(
        MetadataReader metadata,
        CustomAttributeHandleCollection attributes,
        string attributeName)
    {
        foreach (var handle in attributes)
        {
            var attribute = metadata.GetCustomAttribute(handle);
            if (AttributeType(metadata, attribute.Constructor) != attributeName)
            {
                continue;
            }

            var reader = metadata.GetBlobReader(attribute.Value);
            if (reader.RemainingBytes < 3 || reader.ReadUInt16() != 1)
            {
                return null;
            }

            return reader.ReadByte();
        }

        return null;
    }

    private static string AttributeType(
        MetadataReader metadata,
        EntityHandle constructor)
    {
        if (constructor.Kind == HandleKind.MemberReference)
        {
            return MetadataTypeNames.Entity(
                metadata,
                metadata.GetMemberReference(
                    (MemberReferenceHandle)constructor).Parent);
        }

        if (constructor.Kind == HandleKind.MethodDefinition)
        {
            var method = metadata.GetMethodDefinition(
                (MethodDefinitionHandle)constructor);
            return MetadataTypeNames.Definition(
                metadata,
                method.GetDeclaringType());
        }

        return string.Empty;
    }
}
