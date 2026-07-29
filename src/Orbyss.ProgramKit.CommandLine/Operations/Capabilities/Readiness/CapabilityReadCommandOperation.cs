using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Readiness;

/// <summary>Catalog, preflight, capability-read, and resource-read transport.</summary>
public sealed class CapabilityReadCommandOperation : ICommandOperation
{
    private static readonly UTF8Encoding Utf8 = new(false);
    private readonly string commandKey;
    private readonly ICapabilityReadinessService service;

    /// <summary>Initializes one exact capability read-plane command.</summary>
    public CapabilityReadCommandOperation(
        string commandKey,
        ICapabilityReadinessService service)
    {
        this.commandKey = commandKey ??
            throw new ArgumentNullException(nameof(commandKey));
        this.service = service ??
            throw new ArgumentNullException(nameof(service));
    }

    /// <inheritdoc />
    public string CommandKey => commandKey;

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            return commandKey switch
            {
                "capabilities.catalog" => CommandOperationResult.Success(
                    RenderCatalog(
                        await service.CatalogAsync(
                            invocation.RequiredOption("workspace-root"),
                            cancellationToken).ConfigureAwait(false),
                        invocation.OptionalOption("format") ?? "text")),
                "capabilities.preflight" => CommandOperationResult.Success(
                    RenderOne(
                        await service.EvaluateAsync(
                            invocation.Arguments[0],
                            invocation.RequiredOption("workspace-root"),
                            cancellationToken).ConfigureAwait(false),
                        invocation.OptionalOption("format") ?? "text")),
                "capabilities.read" => CommandOperationResult.Success(
                    await service.ReadCapabilityAsync(
                        invocation.Arguments[0],
                        invocation.RequiredOption("workspace-root"),
                        cancellationToken).ConfigureAwait(false)),
                "capabilities.read-resource" => CommandOperationResult.Success(
                    await service.ReadResourceAsync(
                        invocation.Arguments[0],
                        invocation.RequiredOption("workspace-root"),
                        cancellationToken).ConfigureAwait(false)),
                _ => throw new InvalidOperationException(
                    "The capability read-plane command key is not registered."),
            };
        }
        catch (CapabilityOperationException exception)
        {
            return new CommandOperationResult(
                exception.ExitCode,
                default,
                [
                    new CommandDiagnostic(
                        exception.DiagnosticId,
                        "error",
                        exception.Message,
                        exception.Path),
                ]);
        }
    }

    private static byte[] RenderCatalog(
        ImmutableArray<CapabilityReadinessResult> entries,
        string format)
    {
        if (string.Equals(format, "json", StringComparison.Ordinal))
        {
            using MemoryStream output = new();
            using (Utf8JsonWriter writer = new(output))
            {
                writer.WriteStartObject();
                writer.WriteStartArray("capabilities");
                foreach (var entry in entries)
                {
                    WriteJson(writer, entry);
                }

                writer.WriteEndArray();
                writer.WriteEndObject();
            }

            return output.ToArray();
        }

        if (!string.Equals(format, "text", StringComparison.Ordinal))
        {
            throw new CommandInvocationException(
                "Capability catalog format must be one of: json, text.",
                "/options/format");
        }

        StringBuilder outputText = new();
        foreach (var entry in entries)
        {
            outputText.Append(entry.CapabilityId)
                .Append(": state=")
                .Append(entry.State)
                .Append(", role=")
                .Append(entry.Role)
                .Append(", available=")
                .Append(entry.Availability)
                .Append(", registered=")
                .Append(entry.Registered.ToString().ToLowerInvariant())
                .Append(", fresh=")
                .Append(entry.Fresh.ToString().ToLowerInvariant())
                .Append(", providers=")
                .Append(entry.Providers.IsDefaultOrEmpty
                    ? "-"
                    : string.Join(",", entry.Providers))
                .Append("; ")
                .AppendLine(entry.Reason);
        }

        return Utf8.GetBytes(outputText.ToString());
    }

    private static byte[] RenderOne(
        CapabilityReadinessResult entry,
        string format)
    {
        if (string.Equals(format, "json", StringComparison.Ordinal))
        {
            using MemoryStream output = new();
            using (Utf8JsonWriter writer = new(output))
            {
                WriteJson(writer, entry);
            }

            return output.ToArray();
        }

        if (!string.Equals(format, "text", StringComparison.Ordinal))
        {
            throw new CommandInvocationException(
                "Capability preflight format must be one of: json, text.",
                "/options/format");
        }

        return Utf8.GetBytes(
            string.Concat(
                entry.CapabilityId,
                ": ",
                entry.State,
                "; role=",
                entry.Role,
                "; availability=",
                entry.Availability,
                "; registered=",
                entry.Registered.ToString().ToLowerInvariant(),
                "; fresh=",
                entry.Fresh.ToString().ToLowerInvariant(),
                "; providers=",
                entry.Providers.IsDefaultOrEmpty
                    ? "-"
                    : string.Join(",", entry.Providers),
                "; ",
                entry.Reason,
                Environment.NewLine));
    }

    private static void WriteJson(
        Utf8JsonWriter writer,
        CapabilityReadinessResult entry)
    {
        writer.WriteStartObject();
        writer.WriteString("availability", entry.Availability);
        writer.WriteString("capabilityId", entry.CapabilityId);
        writer.WriteBoolean("fresh", entry.Fresh);
        writer.WriteStartArray("providers");
        foreach (var provider in entry.Providers)
        {
            writer.WriteStringValue(provider);
        }

        writer.WriteEndArray();
        writer.WriteString("reason", entry.Reason);
        writer.WriteBoolean("registered", entry.Registered);
        writer.WriteString("role", entry.Role);
        writer.WriteString("state", entry.State);
        writer.WriteEndObject();
    }
}
