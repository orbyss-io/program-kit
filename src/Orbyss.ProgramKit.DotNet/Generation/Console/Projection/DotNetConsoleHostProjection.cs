using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal sealed record DotNetConsoleHostProjection(
    string ApplicationName,
    string ApplicationVersion,
    string AssemblyName,
    string ConsumerProjectPath,
    DotNetConsoleClrTypeDescriptor FeatureType,
    DotNetConsoleClrTypeDescriptor ValidationResultType,
    int InvalidInvocationExitCode,
    int CancellationExitCode,
    int InternalFailureExitCode,
    int HelpExitCode,
    string CompletionOption,
    ImmutableArray<string> CompletionCandidates,
    ImmutableArray<DotNetConsoleCommandProjection> Commands,
    ImmutableArray<DotNetConsoleCommandTrieNode> CommandTrie);
