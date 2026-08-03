using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Cli.Composition;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Cli.Commands;

public static class HelpCommand
{
    public static OperationResult Help() => OperationResultFactory.Success(PublicCommand.Help, OperationPhase.Completion, EffectState.None, utility: new JsonObject
    {
        ["kind"] = "help",
        ["commands"] = new JsonArray("init", "catalog list", "restore", "prepare", "authority record", "explain", "construct", "evaluate", "session explain", "session install", "session verify", "session remove", "help", "version"),
        ["workspaceGrammar"] = "program-kit <init|restore|prepare> --workspace <path> --request <path> [--format text|json]",
        ["catalogGrammar"] = "program-kit catalog list --workspace <path> --request <path> [--format text|json]",
        ["authorityGrammar"] = "program-kit authority record --workspace <path> --request <path> [--format text|json]",
        ["sessionGrammar"] = "program-kit session <explain|install|verify|remove> --workspace <path> --request <path> [--format text|json]",
        ["effectBearing"] = new JsonArray("init", "restore", "authority record", "construct", "session install", "session remove"),
        ["sessionProtocol"] = "program-kit.session-integration-definition/v1",
        ["installedSessionAdapters"] = new JsonArray("orbyss.program-kit:session-provider:codex@1.0.0"),
    });

    public static OperationResult Version() => OperationResultFactory.Success(PublicCommand.Version, OperationPhase.Completion, EffectState.None, utility: new JsonObject
    {
        ["kind"] = "version",
        ["packageId"] = CliReleaseIdentityProvider.PackageId,
        ["cli"] = CliReleaseIdentityProvider.InvokedVersion,
        ["toolCommand"] = CliReleaseIdentityProvider.ToolCommandName,
        ["kernelProtocol"] = "1.0.0",
        ["sessionIntegrationProtocol"] = "1.0.0",
        ["sessionProviderCatalog"] = "1.0.0",
        ["canonicalProfile"] = "program-kit.canonical-json/v1",
    });
}
