using System.Text;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>
/// Deterministic text/JSON projection of the packaged Console contract style.
/// </summary>
public sealed class DescribeConsoleContractCommandOperation : ICommandOperation
{
    private readonly IConsumerCapabilityPayload payload;
    private readonly IProgramKitJsonSerializer serializer;

    /// <summary>Initializes the operation from the exact packaged payload.</summary>
    public DescribeConsoleContractCommandOperation(
        IConsumerCapabilityPayload payload,
        IProgramKitJsonSerializer serializer)
    {
        this.payload = payload ??
            throw new ArgumentNullException(nameof(payload));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.describe-console-contract";

    /// <inheritdoc />
    public ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        _ = cancellationToken;
        var bytes = payload.ReadResource("dotnet-console-contract-style");
        if (string.Equals(
                invocation.OptionalOption("format") ?? "text",
                "json",
                StringComparison.Ordinal))
        {
            return ValueTask.FromResult(CommandOperationResult.Success(bytes));
        }

        var catalog = serializer.Read<DotNetConsoleContractStyleCatalog>(
            bytes,
            DotNetJsonProfiles.ShellBootstrap.Reference,
            JsonSerializationLimits.Default);
        StringBuilder text = new();
        _ = text.Append("Open Console contract style ")
            .Append(catalog.Version)
            .Append(" (Open Console ")
            .Append(catalog.OpenConsoleVersion)
            .AppendLine(")");
        foreach (var rule in catalog.Rules)
        {
            _ = text.Append("- ")
                .Append(rule.Id)
                .Append(": ")
                .AppendLine(rule.Summary);
        }

        _ = text.AppendLine("Commands:")
            .Append("  scaffold: ")
            .AppendLine(catalog.Commands.Scaffold)
            .Append("  materialize: ")
            .AppendLine(catalog.Commands.Materialize);
        return ValueTask.FromResult(
            CommandOperationResult.Success(Encoding.UTF8.GetBytes(text.ToString())));
    }
}
