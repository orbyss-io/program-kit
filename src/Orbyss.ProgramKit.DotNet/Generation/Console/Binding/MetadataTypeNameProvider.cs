using System.Globalization;
using System.Reflection.Metadata;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

internal readonly struct MetadataTypeNameProvider :
    ISignatureTypeProvider<string, object?>
{
    public string GetArrayType(string elementType, ArrayShape shape) =>
        string.Concat(elementType, "[", new string(',', shape.Rank - 1), "]");

    public string GetByReferenceType(string elementType) =>
        string.Concat(elementType, "&");

    public string GetFunctionPointerType(MethodSignature<string> signature) =>
        "method-pointer";

    public string GetGenericInstantiation(
        string genericType,
        ImmutableArray<string> typeArguments) =>
        string.Concat(
            genericType,
            "<",
            string.Join(",", typeArguments),
            ">");

    public string GetGenericMethodParameter(object? genericContext, int index) =>
        string.Concat("!!", index.ToString(CultureInfo.InvariantCulture));

    public string GetGenericTypeParameter(object? genericContext, int index) =>
        string.Concat("!", index.ToString(CultureInfo.InvariantCulture));

    public string GetModifiedType(
        string modifierType,
        string unmodifiedType,
        bool isRequired) =>
        unmodifiedType;

    public string GetPinnedType(string elementType) => elementType;

    public string GetPointerType(string elementType) =>
        string.Concat(elementType, "*");

    public string GetPrimitiveType(PrimitiveTypeCode typeCode) =>
        typeCode switch
        {
            PrimitiveTypeCode.Boolean => "System.Boolean",
            PrimitiveTypeCode.Byte => "System.Byte",
            PrimitiveTypeCode.Char => "System.Char",
            PrimitiveTypeCode.Double => "System.Double",
            PrimitiveTypeCode.Int16 => "System.Int16",
            PrimitiveTypeCode.Int32 => "System.Int32",
            PrimitiveTypeCode.Int64 => "System.Int64",
            PrimitiveTypeCode.IntPtr => "System.IntPtr",
            PrimitiveTypeCode.Object => "System.Object",
            PrimitiveTypeCode.SByte => "System.SByte",
            PrimitiveTypeCode.Single => "System.Single",
            PrimitiveTypeCode.String => "System.String",
            PrimitiveTypeCode.TypedReference => "System.TypedReference",
            PrimitiveTypeCode.UInt16 => "System.UInt16",
            PrimitiveTypeCode.UInt32 => "System.UInt32",
            PrimitiveTypeCode.UInt64 => "System.UInt64",
            PrimitiveTypeCode.UIntPtr => "System.UIntPtr",
            PrimitiveTypeCode.Void => "System.Void",
            _ => string.Concat("primitive:", typeCode.ToString()),
        };

    public string GetSZArrayType(string elementType) =>
        string.Concat(elementType, "[]");

    public string GetTypeFromDefinition(
        MetadataReader reader,
        TypeDefinitionHandle handle,
        byte rawTypeKind) =>
        MetadataTypeNames.Definition(reader, handle);

    public string GetTypeFromReference(
        MetadataReader reader,
        TypeReferenceHandle handle,
        byte rawTypeKind) =>
        MetadataTypeNames.Reference(reader, handle);

    public string GetTypeFromSpecification(
        MetadataReader reader,
        object? genericContext,
        TypeSpecificationHandle handle,
        byte rawTypeKind) =>
        reader.GetTypeSpecification(handle).DecodeSignature(this, genericContext);
}
