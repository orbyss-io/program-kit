using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal sealed record DotNetConsoleHostProjection(
    string ApplicationName,
    string ApplicationVersion,
    string AssemblyName,
    string ConsumerProjectPath,
    DotNetConsoleClrTypeDescriptor FeatureType,
    DotNetConsoleClrTypeDescriptor ValidationResultType,
    ImmutableArray<DotNetConsoleCommandProjection> Commands,
    ImmutableArray<DotNetConsoleCommandTrieNode> CommandTrie);
