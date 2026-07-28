using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal sealed record DotNetConsoleValueProjection(
    int ConstructorPosition,
    string ConstructorParameterName,
    DotNetConsoleBindingSourceKind SourceKind,
    string SourceName,
    string PropertyName,
    string PropertyType,
    string ElementType,
    string AttributeTemplate,
    string Summary,
    int ArgumentPosition,
    int MinimumOccurrences,
    int MaximumOccurrences,
    bool Required,
    bool Repeated,
    bool Flag,
    ImmutableArray<string> Conflicts,
    ImmutableArray<string> Prerequisites,
    DotNetConsoleClrTypeDescriptor RequestType,
    DotNetConsoleDefaultDisposition DefaultDisposition);
