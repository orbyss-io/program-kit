using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text.Json;

// Read metadata without executing consumer constructors or loading private dependencies.
var assemblies = new List<object>();
foreach (string path in args)
{
    using var stream = File.OpenRead(path);
    using var pe = new PEReader(stream);
    MetadataReader reader = pe.GetMetadataReader();
    string TypeName(EntityHandle handle) => handle.IsNil ? "" : handle.Kind switch
    {
        HandleKind.TypeDefinition => Definition((TypeDefinitionHandle)handle),
        HandleKind.TypeReference => Reference((TypeReferenceHandle)handle),
        HandleKind.TypeSpecification => "<generic-type-specification>",
        _ => ""
    };
    string Definition(TypeDefinitionHandle handle)
    {
        TypeDefinition type = reader.GetTypeDefinition(handle);
        var parent = type.GetDeclaringType();
        return parent.IsNil ? Join(reader.GetString(type.Namespace), reader.GetString(type.Name))
            : Definition(parent) + "+" + reader.GetString(type.Name);
    }
    string Reference(TypeReferenceHandle handle)
    {
        TypeReference type = reader.GetTypeReference(handle);
        return type.ResolutionScope.Kind == HandleKind.TypeReference
            ? Reference((TypeReferenceHandle)type.ResolutionScope) + "+" + reader.GetString(type.Name)
            : Join(reader.GetString(type.Namespace), reader.GetString(type.Name));
    }
    var types = reader.TypeDefinitions.Select(handle =>
    {
        TypeDefinition type = reader.GetTypeDefinition(handle);
        return new
        {
            name = Definition(handle),
            isInterface = (type.Attributes & TypeAttributes.Interface) != 0,
            baseType = TypeName(type.BaseType),
            interfaces = type.GetInterfaceImplementations().Select(i =>
                TypeName(reader.GetInterfaceImplementation(i).Interface)).ToArray(),
            methods = type.GetMethods().Select(m => reader.GetString(reader.GetMethodDefinition(m).Name)).ToArray()
        };
    }).ToArray();
    assemblies.Add(new
    {
        path = Path.GetFullPath(path),
        name = reader.GetString(reader.GetAssemblyDefinition().Name),
        references = reader.AssemblyReferences.Select(h => reader.GetString(reader.GetAssemblyReference(h).Name)).ToArray(),
        types
    });
}
Console.WriteLine(JsonSerializer.Serialize(assemblies));

static string Join(string space, string name) => string.IsNullOrEmpty(space) ? name : space + "." + name;
