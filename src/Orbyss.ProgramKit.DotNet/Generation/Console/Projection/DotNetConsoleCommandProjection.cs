using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal sealed record DotNetConsoleCommandProjection(
    ImmutableArray<string> Path,
    ImmutableArray<ImmutableArray<string>> Aliases,
    string Summary,
    string Symbol,
    string SettingsTypeName,
    string CommandTypeName,
    string RequestFactoryTypeName,
    DotNetConsoleClrTypeDescriptor RequestType,
    DotNetConsoleClrTypeDescriptor HandlerType,
    DotNetConsoleClrTypeDescriptor? ValidatorType,
    ImmutableArray<DotNetConsoleValueProjection> Values);
