using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Validation;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Schemas;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.CSharpBuildGates;

/// <summary>
/// Thin command transport over the finite registered Workbench gate operations.
/// </summary>
public sealed class CSharpGateCommandService : ICSharpGateCommandService
{
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonSerializer serializer;
    private readonly ICSharpBuildGateOperationService operations;
    private readonly IConsumerCapabilityPayload capabilityPayload;
    private readonly IWorkbenchSchemaValidator schemaValidator;
    private readonly ICommandSchemaSelector schemaSelector;

    /// <summary>Initializes the exact file, serialization, and operation edges.</summary>
    public CSharpGateCommandService(
        ICommandFileSystem fileSystem,
        IProgramKitJsonSerializer serializer,
        ICSharpBuildGateOperationService operations,
        IConsumerCapabilityPayload capabilityPayload,
        IWorkbenchSchemaValidator schemaValidator,
        ICommandSchemaSelector schemaSelector)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
        this.operations = operations ??
            throw new ArgumentNullException(nameof(operations));
        this.capabilityPayload = capabilityPayload ??
            throw new ArgumentNullException(nameof(capabilityPayload));
        this.schemaValidator = schemaValidator ??
            throw new ArgumentNullException(nameof(schemaValidator));
        this.schemaSelector = schemaSelector ??
            throw new ArgumentNullException(nameof(schemaSelector));
    }

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        string commandKey,
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(commandKey);
        ArgumentNullException.ThrowIfNull(invocation);
        return commandKey switch
        {
            "csharp-gate.validate-definition" =>
                await ValidateAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.render-definition" =>
                await RenderAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.scaffold" =>
                await ScaffoldAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.scaffold-lock" =>
                await ScaffoldLockAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.bind" =>
                await BindAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.verify" =>
                await VerifyAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            "csharp-gate.describe-definition" =>
                Describe(invocation),
            "csharp-gate.materialize-definition" =>
                await MaterializeAsync(invocation, cancellationToken)
                    .ConfigureAwait(false),
            _ => throw new InvalidOperationException(
                "The C# gate command is outside the finite catalog."),
        };
    }

    private CommandOperationResult Describe(CommandInvocation invocation)
    {
        var catalog = capabilityPayload.ReadResource(
            "csharp-gate-authoring-catalog");
        return string.Equals(
                invocation.OptionalOption("format") ?? "text",
                "json",
                StringComparison.Ordinal)
            ? CommandOperationResult.Success(catalog)
            : CommandOperationResult.Success(RenderCatalogText(catalog));
    }

    private async ValueTask<CommandOperationResult> MaterializeAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var draft = await fileSystem.ReadAllBytesAsync(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var content = RemoveSingleUtf8Bom(draft);
        var structuralDiagnostics = ValidateDraftStructure(content);
        if (!structuralDiagnostics.IsDefaultOrEmpty)
        {
            return new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
                default,
                structuralDiagnostics);
        }

        CSharpBuildGateDefinitionDocument definition;
        try
        {
            definition = serializer.Read<CSharpBuildGateDefinitionDocument>(
                content,
                CommandLineJsonProfiles.CSharpBuildGates.Reference,
                CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
            definition = Canonicalize(definition);
        }
        catch (Exception exception) when (
            exception is JsonException or InvalidDataException or
            NotSupportedException)
        {
            return Failure(
                "PKCG001",
                string.Concat(
                    "The gate-definition draft cannot be materialized: ",
                    exception.Message),
                "$");
        }

        var semantic = operations.ValidateDefinition(definition);
        if (!semantic.IsValid)
        {
            return new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
                default,
                semantic.Diagnostics.Select(
                        static diagnostic => new CommandDiagnostic(
                            diagnostic.Id,
                            diagnostic.Severity.ToString()
                                .ToLowerInvariant(),
                            diagnostic.Message,
                            diagnostic.Path))
                    .ToImmutableArray());
        }

        var output = invocation.RequiredOption("output");
        RequireNewOutput(output);
        var canonical = serializer.Write(
            definition,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        await fileSystem.WriteAllBytesAsync(
            output,
            canonical.ToArray(),
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success(
            Encoding.UTF8.GetBytes(
                string.Concat(
                    "Materialized C# gate definition at ",
                    Path.GetFullPath(output),
                    ".",
                    Environment.NewLine)));
    }

    private ImmutableArray<CommandDiagnostic> ValidateDraftStructure(
        ReadOnlyMemory<byte> content)
    {
        try
        {
            var duplicateDiagnostics =
                ImmutableArray.CreateBuilder<CommandDiagnostic>();
            Utf8JsonReader reader = new(
                content.Span,
                new JsonReaderOptions
                {
                    AllowTrailingCommas = false,
                    CommentHandling = JsonCommentHandling.Disallow,
                    MaxDepth = CommandLineJsonProfiles.CSharpBuildGates
                        .MaximumLimits.MaxDepth,
                });
            if (!reader.Read())
            {
                throw new JsonException("A JSON document is required.");
            }

            FindDuplicateProperties(ref reader, "$", duplicateDiagnostics);
            if (reader.Read())
            {
                throw new JsonException(
                    "Only one top-level JSON value is permitted.");
            }

            if (duplicateDiagnostics.Count != 0)
            {
                return duplicateDiagnostics.ToImmutable();
            }
        }
        catch (JsonException exception)
        {
            return
            [
                new CommandDiagnostic(
                    "PKCG001",
                    "error",
                    string.Concat(
                        "The gate-definition draft must be strict UTF-8 JSON: ",
                        exception.Message),
                    "$"),
            ];
        }

        var schemaModule = schemaSelector.Resolve(
            "pkid:schema:program-kit:csharp-build-gate-definition@0.1.0-alpha.2",
            out var revision);
        var validation = schemaValidator.Validate(
            content,
            schemaModule,
            revision,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        return validation.Diagnostics.Select(
                static diagnostic => new CommandDiagnostic(
                    diagnostic.Id,
                    diagnostic.Severity.ToString().ToLowerInvariant(),
                    diagnostic.Message,
                    diagnostic.Path))
            .ToImmutableArray();
    }

    private static ReadOnlyMemory<byte> RemoveSingleUtf8Bom(
        ReadOnlyMemory<byte> content)
    {
        ReadOnlySpan<byte> span = content.Span;
        return span.Length >= 3 &&
               span[0] == 0xef &&
               span[1] == 0xbb &&
               span[2] == 0xbf
            ? content[3..]
            : content;
    }

    private static CSharpBuildGateDefinitionDocument Canonicalize(
        CSharpBuildGateDefinitionDocument definition)
    {
        return definition with
        {
            SemanticOwners = definition.SemanticOwners
                .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                .ToImmutableArray(),
            AnalyzerComponents = definition.AnalyzerComponents
                .Select(Canonicalize)
                .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                .ToImmutableArray(),
            RuleCatalog = definition.RuleCatalog with
            {
                Rules = definition.RuleCatalog.Rules
                    .Select(Canonicalize)
                    .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                    .ToImmutableArray(),
                Diagnostics = definition.RuleCatalog.Diagnostics
                    .OrderBy(
                        static value => value.DiagnosticId,
                        StringComparer.Ordinal)
                    .ToImmutableArray(),
            },
            Profiles = definition.Profiles with
            {
                Projects = definition.Profiles.Projects
                    .Select(Canonicalize)
                    .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                    .ToImmutableArray(),
                Inputs = definition.Profiles.Inputs
                    .Select(Canonicalize)
                    .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                    .ToImmutableArray(),
                GeneratedSources = definition.Profiles.GeneratedSources
                    .Select(Canonicalize)
                    .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                    .ToImmutableArray(),
            },
            ActivationMatrix = definition.ActivationMatrix with
            {
                Activations = definition.ActivationMatrix.Activations
                    .Select(Canonicalize)
                    .OrderBy(
                        CSharpBuildGateOrdering.ActivationKey,
                        StringComparer.Ordinal)
                    .ToImmutableArray(),
            },
            TemporaryExceptions = definition.TemporaryExceptions
                .Select(Canonicalize)
                .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                .ToImmutableArray(),
            SuppressionLedger = definition.SuppressionLedger with
            {
                Entries = definition.SuppressionLedger.Entries
                    .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                    .ToImmutableArray(),
            },
            Assurance = definition.Assurance with
            {
                Migrations = definition.Assurance.Migrations
                    .OrderBy(
                        static value => ReferenceKey(value.Source),
                        StringComparer.Ordinal)
                    .ThenBy(
                        static value => ReferenceKey(value.Target),
                        StringComparer.Ordinal)
                    .ToImmutableArray(),
                Threats = definition.Assurance.Threats
                    .Select(Canonicalize)
                    .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                    .ToImmutableArray(),
                Fixtures = definition.Assurance.Fixtures
                    .OrderBy(static value => value.Identity.Value, StringComparer.Ordinal)
                    .ToImmutableArray(),
            },
        };
    }

    private static CSharpAnalyzerComponent Canonicalize(
        CSharpAnalyzerComponent component) =>
        component with
        {
            RuleIds = Sort(component.RuleIds),
            ReceiptGeneratorRevisions =
                Sort(component.ReceiptGeneratorRevisions),
        };

    private static CSharpGateRuleDefinition Canonicalize(
        CSharpGateRuleDefinition rule) =>
        rule with
        {
            ClaimsOutsideRule = rule.ClaimsOutsideRule
                .Order(StringComparer.Ordinal)
                .ToImmutableArray(),
            ProjectProfileIds = Sort(rule.ProjectProfileIds),
            SourceProfileIds = Sort(rule.SourceProfileIds),
        };

    private static CSharpGateProjectProfile Canonicalize(
        CSharpGateProjectProfile profile) =>
        profile with
        {
            TargetFrameworks = profile.TargetFrameworks
                .Order(StringComparer.Ordinal)
                .ToImmutableArray(),
            AllowedProjectDependencies =
                Sort(profile.AllowedProjectDependencies),
            AllowedPackageDependencies =
                Sort(profile.AllowedPackageDependencies),
        };

    private static CSharpGateInputProfile Canonicalize(
        CSharpGateInputProfile profile) =>
        profile with
        {
            Inventory = profile.Inventory
                .OrderBy(
                    static value => value.RepositoryRelativePath,
                    StringComparer.Ordinal)
                .ToImmutableArray(),
            ApplicableRuleIds = Sort(profile.ApplicableRuleIds),
        };

    private static CSharpGateGeneratedSourceProfile Canonicalize(
        CSharpGateGeneratedSourceProfile profile) =>
        profile with
        {
            LogicalHintPaths = profile.LogicalHintPaths
                .Order(StringComparer.Ordinal)
                .ToImmutableArray(),
            Inventory = profile.Inventory
                .OrderBy(
                    static value => value.RepositoryRelativePath,
                    StringComparer.Ordinal)
                .ToImmutableArray(),
            ApplicableRuleIds = Sort(profile.ApplicableRuleIds),
        };

    private static CSharpGateActivation Canonicalize(
        CSharpGateActivation activation) =>
        activation with
        {
            AnalyzerComponentIds = Sort(activation.AnalyzerComponentIds),
        };

    private static CSharpGateTemporaryActivationExceptionRecord Canonicalize(
        CSharpGateTemporaryActivationExceptionRecord exception) =>
        exception with
        {
            ConditionParameters = exception.ConditionParameters
                .OrderBy(static value => value.Name, StringComparer.Ordinal)
                .ThenBy(static value => value.Value, StringComparer.Ordinal)
                .ToImmutableArray(),
            CompensatingVerification =
                Sort(exception.CompensatingVerification),
            EvidenceRequirements = Sort(exception.EvidenceRequirements),
        };

    private static CSharpGateThreat Canonicalize(CSharpGateThreat threat) =>
        threat with
        {
            Mitigations = Sort(threat.Mitigations),
        };

    private static ImmutableArray<ProgramKitIdentifier> Sort(
        ImmutableArray<ProgramKitIdentifier> values) =>
        values
            .OrderBy(static value => value.Value, StringComparer.Ordinal)
            .ToImmutableArray();

    private static ImmutableArray<ArtifactReference> Sort(
        ImmutableArray<ArtifactReference> values) =>
        values
            .OrderBy(ReferenceKey, StringComparer.Ordinal)
            .ToImmutableArray();

    private static string ReferenceKey(ArtifactReference value) =>
        string.Join(
            "@",
            value.Identity.Value,
            value.Version.ToString());

    private static void FindDuplicateProperties(
        ref Utf8JsonReader reader,
        string path,
        ImmutableArray<CommandDiagnostic>.Builder diagnostics)
    {
        if (reader.TokenType == JsonTokenType.StartObject)
        {
            HashSet<string> names = new(StringComparer.Ordinal);
            while (reader.Read() &&
                   reader.TokenType != JsonTokenType.EndObject)
            {
                if (reader.TokenType != JsonTokenType.PropertyName)
                {
                    throw new JsonException(
                        "An object property name was expected.");
                }

                var name = reader.GetString() ??
                    throw new JsonException(
                        "An object property name cannot be null.");
                var childPath = string.Concat(path, ".", name);
                if (!names.Add(name))
                {
                    diagnostics.Add(
                        new CommandDiagnostic(
                            "PKCG001",
                            "error",
                            string.Concat(
                                "JSON property '",
                                name,
                                "' occurs more than once."),
                            childPath));
                }

                if (!reader.Read())
                {
                    throw new JsonException(
                        "An object property value was expected.");
                }

                FindDuplicateProperties(
                    ref reader,
                    childPath,
                    diagnostics);
            }

            return;
        }

        if (reader.TokenType == JsonTokenType.StartArray)
        {
            var index = 0;
            while (reader.Read() &&
                   reader.TokenType != JsonTokenType.EndArray)
            {
                FindDuplicateProperties(
                    ref reader,
                    string.Concat(path, "[", index, "]"),
                    diagnostics);
                index++;
            }
        }
    }

    private static byte[] RenderCatalogText(ReadOnlyMemory<byte> catalog)
    {
        return Encoding.UTF8.GetBytes(
            string.Concat(
                "Exact C# gate authoring catalog:",
                Environment.NewLine,
                Encoding.UTF8.GetString(catalog.Span),
                Environment.NewLine));
    }

    private static CommandOperationResult Failure(
        string id,
        string message,
        string path) =>
        new(
            CommandExitCode.ConformanceFailure,
            default,
            [new CommandDiagnostic(id, "error", message, path)]);

    private async ValueTask<CommandOperationResult> ValidateAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var definition = await ReadAsync<CSharpBuildGateDefinitionDocument>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var validation = operations.ValidateDefinition(definition);
        return validation.IsValid
            ? CommandOperationResult.Success()
            : new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
                default,
                validation.Diagnostics
                    .Select(diagnostic => new CommandDiagnostic(
                        diagnostic.Id,
                        diagnostic.Severity.ToString().ToLowerInvariant(),
                        diagnostic.Message,
                        diagnostic.Path))
                    .ToImmutableArray());
    }

    private async ValueTask<CommandOperationResult> RenderAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var definition = await ReadAsync<CSharpBuildGateDefinitionDocument>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var output = invocation.RequiredOption("output");
        RequireNewOutput(output);
        var rendered = operations.RenderDefinition(definition);
        await fileSystem.WriteAllBytesAsync(
            output,
            Encoding.UTF8.GetBytes(rendered),
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success();
    }

    private async ValueTask<CommandOperationResult> ScaffoldAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var request = await ReadAsync<ConsumerAnalyzerScaffoldRequest>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        _ = await operations.ScaffoldAsync(
            request,
            invocation.RequiredOption("output"),
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success();
    }

    private async ValueTask<CommandOperationResult> ScaffoldLockAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var root = Path.GetFullPath(
            invocation.RequiredOption("repository-root"));
        if (!fileSystem.DirectoryExists(root))
        {
            throw new IOException(
                "The exact repository root does not exist.");
        }

        var definitionPath = ResolveBelow(
            root,
            invocation.Arguments[0],
            "The gate definition");
        var intentPath = ResolveBelow(
            root,
            invocation.Arguments[1],
            "The lock intent");
        var output = ResolveBelow(
            root,
            invocation.RequiredOption("output"),
            "The scaffold output");
        RequireNewOutput(output);
        var definition = await ReadAsync<CSharpBuildGateDefinitionDocument>(
            definitionPath,
            cancellationToken).ConfigureAwait(false);
        var intent = await ReadAsync<CSharpGateLockIntent>(
            intentPath,
            cancellationToken).ConfigureAwait(false);
        var relativeDefinition = Path.GetRelativePath(
                root,
                definitionPath)
            .Replace('\\', '/');
        var request = operations.ScaffoldLock(
            definition,
            relativeDefinition,
            intent,
            root);
        var canonical = serializer.Write(
            request,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
        await PromoteFileAsync(
            output,
            canonical.ToArray(),
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success(
            Encoding.UTF8.GetBytes(
                string.Concat(
                    "Scaffolded exact C# gate bind request at ",
                    output,
                    ".",
                    Environment.NewLine)));
    }

    private async ValueTask<CommandOperationResult> BindAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var requestBytes = await fileSystem.ReadAllBytesAsync(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var output = invocation.RequiredOption("output");
        RequireNewOutput(output);
        byte[] canonical;
        if (IsAlphaOneBindRequest(requestBytes.Span))
        {
            var request = serializer.Read<CSharpGateBindRequestAlpha1>(
                requestBytes,
                CommandLineJsonProfiles.CSharpBuildGates.Reference,
                CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
            var selectionLock = operations.Bind(request);
            canonical = serializer.Write(
                selectionLock,
                CommandLineJsonProfiles.CSharpBuildGates.Reference,
                CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits)
                .ToArray();
        }
        else
        {
            var request = serializer.Read<CSharpGateBindRequest>(
                requestBytes,
                CommandLineJsonProfiles.CSharpBuildGates.Reference,
                CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
            var selectionLock = operations.Bind(request);
            canonical = serializer.Write(
                selectionLock,
                CommandLineJsonProfiles.CSharpBuildGates.Reference,
                CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits)
                .ToArray();
        }

        await PromoteFileAsync(
            output,
            canonical,
            cancellationToken).ConfigureAwait(false);
        return CommandOperationResult.Success();
    }

    private async ValueTask<CommandOperationResult> VerifyAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        var request = await ReadAsync<CSharpGateVerificationRequest>(
            invocation.Arguments[0],
            cancellationToken).ConfigureAwait(false);
        var output = invocation.RequiredOption("output");
        RequireNewOutput(output);
        var result = await operations.VerifyAsync(
            request with { EvidenceOutputPath = output },
            cancellationToken).ConfigureAwait(false);
        return result.Succeeded
            ? CommandOperationResult.Success()
            : new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
                default,
                [
                    new CommandDiagnostic(
                        "PKCG070",
                        "error",
                        string.Concat(
                            "C# gate verification failed at ",
                            result.FailureLayer?.ToString() ?? "unknown",
                            "."),
                        "/verification"),
                ]);
    }

    private async ValueTask<T> ReadAsync<T>(
        string path,
        CancellationToken cancellationToken)
    {
        var bytes = await fileSystem.ReadAllBytesAsync(
            path,
            cancellationToken).ConfigureAwait(false);
        return serializer.Read<T>(
            bytes,
            CommandLineJsonProfiles.CSharpBuildGates.Reference,
            CommandLineJsonProfiles.CSharpBuildGates.MaximumLimits);
    }

    private void RequireNewOutput(string path)
    {
        if (fileSystem.FileExists(path) || fileSystem.DirectoryExists(path))
        {
            throw new IOException(
                "The exact operation output already exists.");
        }
    }

    private static bool IsAlphaOneBindRequest(ReadOnlySpan<byte> content)
    {
        Utf8JsonReader reader = new(
            content,
            new JsonReaderOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
                MaxDepth = CommandLineJsonProfiles.CSharpBuildGates
                    .MaximumLimits.MaxDepth,
            });
        if (!reader.Read() || reader.TokenType != JsonTokenType.StartObject)
        {
            return false;
        }

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                return false;
            }

            var name = reader.GetString();
            if (!reader.Read())
            {
                return false;
            }

            if (string.Equals(name, "version", StringComparison.Ordinal))
            {
                return reader.TokenType == JsonTokenType.String &&
                    string.Equals(
                        reader.GetString(),
                        "0.1.0-alpha.1",
                        StringComparison.Ordinal);
            }

            reader.Skip();
        }

        return false;
    }

    private static string ResolveBelow(
        string root,
        string path,
        string description)
    {
        var candidate = Path.GetFullPath(path, root);
        var prefix = string.Concat(
            root.TrimEnd(
                Path.DirectorySeparatorChar,
                Path.AltDirectorySeparatorChar),
            Path.DirectorySeparatorChar);
        if (!candidate.StartsWith(
                prefix,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new IOException(
                string.Concat(description, " escapes the repository root."));
        }

        return candidate;
    }

    private async ValueTask PromoteFileAsync(
        string output,
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        var stage = string.Concat(output, ".program-kit-stage");
        RequireNewOutput(stage);
        try
        {
            await fileSystem.WriteAllBytesAsync(
                stage,
                content,
                cancellationToken).ConfigureAwait(false);
            fileSystem.MoveFile(stage, output, overwrite: false);
        }
        finally
        {
            if (fileSystem.FileExists(stage))
            {
                fileSystem.DeleteFile(stage);
            }
        }
    }
}
