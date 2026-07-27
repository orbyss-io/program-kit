using System.Security.Cryptography;
using System.Text;

namespace Orbyss.ProgramKit.DotNet.Generation.ConsoleCommands;

/// <summary>Exact generated Console command-dispatch contract and deterministic artifact paths.</summary>
internal static class DotNetConsoleCommandDispatchContract
{
    internal const string DispatcherContractPath =
        "ProgramKitGenerated/Commands/IProgramKitConsoleCommandDispatcher.cs";
    internal const string DispatchLockPath =
        "ProgramKitGenerated/Commands/console-command-dispatch.lock.json";
    internal const string DispatchEvidencePath =
        "ProgramKitGenerated/Evidence/console-command-dispatch.evidence.json";
    internal const string ParserPath =
        "ProgramKitGenerated/Commands/GeneratedConsoleParser.cs";
    internal const string ParseResultPath =
        "ProgramKitGenerated/Commands/GeneratedConsoleParseResult.cs";
    internal const string RegistrationMethod =
        "ConfigureProgramKitConsoleServices";
    internal const string ExitCodePolicy =
        "return-dispatcher-integer-unchanged";
    internal const string LockSchema =
        "pkid:schema:program-kit:dotnet-console-command-dispatch-lock@1.0.0";
    internal const string EvidenceSchema =
        "pkid:schema:program-kit:dotnet-console-command-dispatch-evidence@1.0.0";
    internal const string DispatcherSource =
        "namespace GeneratedHost.Commands;\n" +
        "\n" +
        "internal interface IProgramKitConsoleCommandDispatcher\n" +
        "{\n" +
        "    ValueTask<int> DispatchAsync(\n" +
        "        GeneratedConsoleParseResult parseResult,\n" +
        "        CancellationToken cancellationToken);\n" +
        "}\n";

    internal static readonly ImmutableArray<string> LifecycleOrder =
    [
        "parse",
        "compose",
        "resolve-single-dispatcher",
        "start-host",
        "dispatch-once",
        "stop-host-finally",
        "return-dispatcher-integer-unchanged",
    ];

    internal static ArtifactReference DispatcherRevision { get; } =
        new(
            new ProgramKitIdentifier(
                "pkid:contract:program-kit:console-command-dispatcher"),
            new SemanticVersion("1.0.0"),
            Digest(Encoding.UTF8.GetBytes(DispatcherSource)));

    private static Sha256Digest Digest(ReadOnlySpan<byte> content) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(content))));
}
