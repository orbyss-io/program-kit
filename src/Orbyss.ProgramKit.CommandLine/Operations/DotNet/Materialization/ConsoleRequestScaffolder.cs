using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text.Json;
using System.Xml;
using System.Xml.Linq;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.OpenConsole.Contracts.Validation;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>
/// Deterministic Console request scaffolder. It reads only the explicitly
/// selected sketch, project, and supplied artifacts; it performs no restore,
/// build, source inspection, or repository discovery.
/// </summary>
public sealed class ConsoleRequestScaffolder : IConsoleRequestScaffolder
{
    private const string AuthoringMarker =
        ".agent-capabilities/authoring-workspace.json";
    private const string SketchSchema =
        "pkid:schema:program-kit:dotnet-console-command-sketch@0.1.0-alpha.1";
    private const string ContractStyle =
        "pkid:contract-style:program-kit:open-console@0.1.0-alpha.2";
    private const string RequestSchema =
        "pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.2";
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonSerializer serializer;
    private readonly ICommandSchemaSelector schemaSelector;
    private readonly IWorkbenchSchemaValidator schemaValidator;
    private readonly IDotNetShellValidator shellValidator;
    private readonly IProgramKitSemanticValidator<OpenConsoleDocumentAlpha2>
        openConsoleValidator;
    private readonly IDotNetConsoleBindingValidator bindingValidator;

    /// <summary>Initializes every explicit scaffold collaborator.</summary>
    public ConsoleRequestScaffolder(
        ICommandFileSystem fileSystem,
        IProgramKitJsonSerializer serializer,
        ICommandSchemaSelector schemaSelector,
        IWorkbenchSchemaValidator schemaValidator,
        IDotNetShellValidator shellValidator,
        IProgramKitSemanticValidator<OpenConsoleDocumentAlpha2>
            openConsoleValidator,
        IDotNetConsoleBindingValidator bindingValidator)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
        this.schemaSelector = schemaSelector ??
            throw new ArgumentNullException(nameof(schemaSelector));
        this.schemaValidator = schemaValidator ??
            throw new ArgumentNullException(nameof(schemaValidator));
        this.shellValidator = shellValidator ??
            throw new ArgumentNullException(nameof(shellValidator));
        this.openConsoleValidator = openConsoleValidator ??
            throw new ArgumentNullException(nameof(openConsoleValidator));
        this.bindingValidator = bindingValidator ??
            throw new ArgumentNullException(nameof(bindingValidator));
    }

    /// <inheritdoc />
    public async ValueTask<string> ScaffoldAsync(
        string sketchPath,
        string workspaceRoot,
        string consumerProjectPath,
        string outputPath,
        CancellationToken cancellationToken)
    {
        var paths = PreflightPaths(
            sketchPath,
            workspaceRoot,
            consumerProjectPath,
            outputPath);
        var sketchBytes = await fileSystem.ReadAllBytesAsync(
            paths.SketchPath,
            cancellationToken).ConfigureAwait(false);
        ValidateNoPlaceholders(sketchBytes);
        ValidateSchema(sketchBytes, SketchSchema);
        var sketch = Read<DotNetConsoleCommandSketch>(sketchBytes, "/sketch");
        ValidateSketch(sketch, paths);
        var project = await ReadProjectAsync(
            paths.ProjectPath,
            cancellationToken).ConfigureAwait(false);
        await VerifySuppliedArtifactsAsync(
            sketch,
            paths.WorkspaceRoot,
            cancellationToken).ConfigureAwait(false);
        var request = CreateRequest(sketch, paths.ProjectRelativePath, project);
        var requestBytes = serializer.Write(
            request,
            DotNetJsonProfiles.ShellBootstrap.Reference,
            JsonSerializationLimits.Default).ToArray();
        ValidateSchema(requestBytes, RequestSchema);
        _ = Read<DotNetConsoleInputMaterializationRequestAlpha2>(
            requestBytes,
            "/request");
        ValidateRequest(request, project);
        await PromoteAsync(paths, requestBytes, cancellationToken)
            .ConfigureAwait(false);
        return paths.OutputPath;
    }

    private ConsoleRequestScaffoldPaths PreflightPaths(
        string sketchPath,
        string workspaceRoot,
        string consumerProjectPath,
        string outputPath)
    {
        try
        {
            var workspace = Path.GetFullPath(workspaceRoot);
            LocalOperationPaths.EnsureSafeRoot(workspace);
            if (!fileSystem.DirectoryExists(workspace))
            {
                throw new InvalidDataException(
                    "The explicit consumer workspace does not exist.");
            }

            var marker = LocalOperationPaths.ResolveBelow(
                workspace,
                AuthoringMarker,
                "The authoring marker");
            if (fileSystem.FileExists(marker))
            {
                throw new InvalidDataException(
                    "Program Kit product operations cannot scaffold consumer inputs in its authoring workspace.");
            }

            LocalOperationPaths.RequireNormalizedRelativePath(
                consumerProjectPath,
                "The consumer project path");
            if (!consumerProjectPath.EndsWith(
                    ".csproj",
                    StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidDataException(
                    "The consumer project must select one relative .csproj.");
            }

            var sketch = Path.GetFullPath(sketchPath, workspace);
            var project = LocalOperationPaths.ResolveBelow(
                workspace,
                consumerProjectPath,
                "The consumer project path");
            var output = Path.GetFullPath(outputPath, workspace);
            _ = LocalOperationPaths.RelativeTo(workspace, sketch);
            _ = LocalOperationPaths.RelativeTo(workspace, output);
            if (!fileSystem.FileExists(sketch) ||
                !fileSystem.FileExists(project))
            {
                throw new InvalidDataException(
                    "The exact sketch and consumer project must exist.");
            }

            if (fileSystem.FileExists(output) ||
                fileSystem.DirectoryExists(output))
            {
                throw new InvalidDataException(
                    "The scaffold output must be a new path.");
            }

            var stage = string.Concat(output, ".program-kit-staging");
            if (fileSystem.FileExists(stage) ||
                fileSystem.DirectoryExists(stage))
            {
                throw new InvalidDataException(
                    "A prior Console request staging artifact requires bounded cleanup.");
            }

            return new ConsoleRequestScaffoldPaths(
                workspace,
                sketch,
                project,
                consumerProjectPath,
                output,
                stage);
        }
        catch (ConsoleRequestScaffoldingException)
        {
            throw;
        }
        catch (Exception exception) when (
            exception is ArgumentException or
                IOException or
                InvalidDataException or
                UnauthorizedAccessException)
        {
            throw new ConsoleRequestScaffoldingException(
                exception.Message,
                "/paths");
        }
    }

    private void ValidateSchema(ReadOnlyMemory<byte> content, string schemaId)
    {
        try
        {
            var module = schemaSelector.Resolve(schemaId, out var revision);
            var result = schemaValidator.Validate(
                content,
                module,
                revision,
                JsonSerializationLimits.Default);
            if (!result.IsValid)
            {
                var diagnostic = result.Diagnostics[0];
                throw new ConsoleRequestScaffoldingException(
                    diagnostic.Message,
                    diagnostic.Path);
            }
        }
        catch (ConsoleRequestScaffoldingException)
        {
            throw;
        }
        catch (Exception exception) when (
            exception is ArgumentException or
                InvalidDataException or
                InvalidOperationException)
        {
            throw new ConsoleRequestScaffoldingException(
                exception.Message,
                "/$schema");
        }
    }

    private T Read<T>(ReadOnlyMemory<byte> content, string prefix)
    {
        try
        {
            return serializer.Read<T>(
                content,
                DotNetJsonProfiles.ShellBootstrap.Reference,
                JsonSerializationLimits.Default);
        }
        catch (ProgramKitJsonException exception)
        {
            throw new ConsoleRequestScaffoldingException(
                exception.Message,
                string.IsNullOrEmpty(exception.Diagnostic.Path)
                    ? prefix
                    : string.Concat(prefix, exception.Diagnostic.Path));
        }
        catch (Exception exception) when (
            exception is ArgumentException or InvalidDataException)
        {
            throw new ConsoleRequestScaffoldingException(
                exception.Message,
                prefix);
        }
    }

    private void ValidateSketch(
        DotNetConsoleCommandSketch sketch,
        ConsoleRequestScaffoldPaths paths)
    {
        if (!string.Equals(sketch.Schema, SketchSchema, StringComparison.Ordinal) ||
            sketch.Version != new SemanticVersion("0.1.0-alpha.1") ||
            !string.Equals(
                sketch.ContractStyle,
                ContractStyle,
                StringComparison.Ordinal) ||
            sketch.Configuration is not ("Debug" or "Release") ||
            sketch.Platform != "AnyCPU" ||
            sketch.SuppliedArtifacts.IsDefaultOrEmpty)
        {
            throw new ConsoleRequestScaffoldingException(
                "The sketch must initialize the exact alpha.1 sketch and alpha.2 contract style.",
                "/sketch");
        }

        var shellResult = shellValidator.Validate(sketch.Shell);
        if (!shellResult.IsValid)
        {
            throw new ConsoleRequestScaffoldingException(
                shellResult.Diagnostics[0].Message,
                shellResult.Diagnostics[0].Path);
        }

        var hosts = sketch.Shell.Hosts.Where(host =>
            host.Identity == sketch.HostIdentity &&
            host.Kind == DotNetHostKind.Console).ToArray();
        if (hosts.Length != 1 ||
            sketch.OpenConsole.HostRevision.Identity != sketch.HostIdentity ||
            sketch.OpenConsole.HostRevision.Version != hosts[0].Version)
        {
            throw new ConsoleRequestScaffoldingException(
                "The sketch must select exactly one Console host and its exact revision.",
                "/sketch/hostIdentity");
        }

        if (sketch.OpenConsole.Commands.IsDefaultOrEmpty ||
            sketch.Binding.Operations.IsDefaultOrEmpty)
        {
            throw new ConsoleRequestScaffoldingException(
                "The sketch must supply complete command and binding semantics.",
                "/sketch/openConsole/commands");
        }

        ValidateExactOperationSets(sketch, hosts[0]);
        _ = paths;
    }

    private static void ValidateExactOperationSets(
        DotNetConsoleCommandSketch sketch,
        DotNetHostDefinition host)
    {
        var commandKeys = sketch.OpenConsole.Commands
            .Select(static command => Exact(command.OperationRevision))
            .ToArray();
        var hostKeys = host.OperationBindings
            .Select(static binding =>
                Exact(binding.OperationContract.OperationRevision))
            .ToArray();
        var bindingKeys = sketch.Binding.Operations
            .Select(static binding => Exact(binding.OperationRevision))
            .ToArray();
        var provenanceKeys = sketch.OpenConsole.OperationRevisions
            .Select(Exact)
            .ToArray();
        if (HasDuplicates(commandKeys) ||
            HasDuplicates(hostKeys) ||
            HasDuplicates(bindingKeys) ||
            HasDuplicates(provenanceKeys) ||
            !ExactSet(commandKeys, hostKeys) ||
            !ExactSet(commandKeys, bindingKeys) ||
            !ExactSet(commandKeys, provenanceKeys))
        {
            throw new ConsoleRequestScaffoldingException(
                "Console commands, shell operation bindings, typed bindings, and operation provenance must select one identical exact operation set.",
                "/sketch/openConsole/operationRevisions");
        }
    }

    private async ValueTask<ConsoleProjectMechanics> ReadProjectAsync(
        string projectPath,
        CancellationToken cancellationToken)
    {
        var content = await fileSystem.ReadAllBytesAsync(
            projectPath,
            cancellationToken).ConfigureAwait(false);
        var bytes = content.ToArray();
        if (bytes.Length >= 3 &&
            bytes[0] == 0xef &&
            bytes[1] == 0xbb &&
            bytes[2] == 0xbf)
        {
            throw new ConsoleRequestScaffoldingException(
                "The exact consumer project must be BOM-less UTF-8 XML.",
                "/consumer-project");
        }

        using var stream = new MemoryStream(bytes, writable: false);
        using var reader = XmlReader.Create(
            stream,
            new XmlReaderSettings
            {
                DtdProcessing = DtdProcessing.Prohibit,
                IgnoreComments = false,
                IgnoreWhitespace = false,
            });
        var document = XDocument.Load(reader, LoadOptions.PreserveWhitespace);
        var targetFrameworks = Values(document, "TargetFramework");
        var pluralFrameworks = Values(document, "TargetFrameworks");
        if (pluralFrameworks.Length != 0 ||
            targetFrameworks.Length != 1 ||
            targetFrameworks[0] != "net10.0")
        {
            throw new ConsoleRequestScaffoldingException(
                "The exact project must declare one unambiguous net10.0 TargetFramework.",
                "/consumer-project/TargetFramework");
        }

        var assemblyNames = Values(document, "AssemblyName");
        if (assemblyNames.Length > 1)
        {
            throw new ConsoleRequestScaffoldingException(
                "The exact project declares ambiguous AssemblyName values.",
                "/consumer-project/AssemblyName");
        }

        var name = assemblyNames.Length == 1
            ? assemblyNames[0]
            : Path.GetFileNameWithoutExtension(projectPath);
        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ConsoleRequestScaffoldingException(
                "The consumer project name could not be derived mechanically.",
                "/consumer-project/AssemblyName");
        }

        return new ConsoleProjectMechanics(name, targetFrameworks[0]);
    }

    private async ValueTask VerifySuppliedArtifactsAsync(
        DotNetConsoleCommandSketch sketch,
        string workspaceRoot,
        CancellationToken cancellationToken)
    {
        HashSet<string> outputs = new(StringComparer.Ordinal);
        HashSet<string> revisions = new(StringComparer.Ordinal);
        for (var index = 0; index < sketch.SuppliedArtifacts.Length; index++)
        {
            var supplied = sketch.SuppliedArtifacts[index];
            try
            {
                LocalOperationPaths.RequireNormalizedRelativePath(
                    supplied.WorkspaceRelativePath,
                    "The supplied artifact path");
                LocalOperationPaths.RequireNormalizedRelativePath(
                    supplied.OutputRelativePath,
                    "The supplied artifact output path");
                var source = LocalOperationPaths.ResolveBelow(
                    workspaceRoot,
                    supplied.WorkspaceRelativePath,
                    "The supplied artifact path");
                if (!fileSystem.FileExists(source))
                {
                    throw new InvalidDataException(
                        "The exact supplied artifact does not exist.");
                }

                var bytes = await fileSystem.ReadAllBytesAsync(
                    source,
                    cancellationToken).ConfigureAwait(false);
                var digest = string.Concat(
                    "sha256:",
                    Convert.ToHexString(SHA256.HashData(bytes.Span))
                        .ToLowerInvariant());
                if (!string.Equals(
                        digest,
                        supplied.Revision.Digest.Value,
                        StringComparison.Ordinal) ||
                    !outputs.Add(supplied.OutputRelativePath) ||
                    !revisions.Add(Exact(supplied.Revision)))
                {
                    throw new InvalidDataException(
                        "Supplied artifact bytes, output paths, and exact revisions must be fresh and unique.");
                }
            }
            catch (Exception exception) when (
                exception is ArgumentException or
                    IOException or
                    InvalidDataException)
            {
                throw new ConsoleRequestScaffoldingException(
                    exception.Message,
                    string.Concat("/sketch/suppliedArtifacts/", index));
            }
        }
    }

    private static DotNetConsoleInputMaterializationRequestAlpha2 CreateRequest(
        DotNetConsoleCommandSketch sketch,
        string projectPath,
        ConsoleProjectMechanics project)
    {
        var host = sketch.Shell.Hosts.Single(candidate =>
            candidate.Identity == sketch.HostIdentity &&
            candidate.Kind == DotNetHostKind.Console);
        var commands = sketch.OpenConsole.Commands.Select(command =>
        {
            var binding = host.OperationBindings.Single(candidate =>
                candidate.OperationContract.OperationRevision ==
                    command.OperationRevision);
            return new OpenConsoleCommandAlpha2(
                command.OperationRevision,
                command.Path,
                command.Aliases,
                command.Summary,
                command.Arguments,
                command.Options,
                command.StandardInput,
                command.StandardOutput,
                command.StandardError,
                Sort(binding.GetInputSchemaRevisions()),
                Sort(binding.GetResultSchemaRevisions()),
                Sort(binding.GetDiagnosticSchemaRevisions()),
                command.ExitCodes,
                command.AuthorityRevision,
                command.Examples,
                command.Deprecation);
        }).ToImmutableArray();
        DotNetConsoleOpenConsoleIntentAlpha2 openConsole = new(
            "pkid:schema:program-kit:open-console@0.1.0-alpha.2",
            new SemanticVersion("0.1.0-alpha.2"),
            sketch.OpenConsole.Info,
            sketch.OpenConsole.HostRevision,
            sketch.OpenConsole.Parsing,
            sketch.OpenConsole.HostExitCodeRoles,
            sketch.OpenConsole.GlobalOptions,
            commands,
            sketch.OpenConsole.Help,
            sketch.OpenConsole.Completion,
            sketch.OpenConsole.Compatibility,
            sketch.OpenConsole.GeneratorRevision,
            sketch.OpenConsole.OperationRevisions);
        return new DotNetConsoleInputMaterializationRequestAlpha2(
            RequestSchema,
            new SemanticVersion("0.1.0-alpha.2"),
            sketch.Identity,
            sketch.OwnerIdentity,
            sketch.OutputSetIdentity,
            sketch.HostIdentity,
            projectPath,
            sketch.ConsumerProjectIdentity,
            project.AssemblyName,
            project.TargetFramework,
            sketch.Configuration,
            sketch.Platform,
            sketch.Shell,
            openConsole,
            sketch.Binding,
            sketch.SuppliedArtifacts);
    }

    private void ValidateRequest(
        DotNetConsoleInputMaterializationRequestAlpha2 request,
        ConsoleProjectMechanics project)
    {
        var host = request.Shell.Hosts.Single(candidate =>
            candidate.Identity == request.HostIdentity &&
            candidate.Kind == DotNetHostKind.Console);
        OpenConsoleDocumentAlpha2 document = new(
            request.OpenConsole.Schema,
            request.OpenConsole.DocumentVersion,
            request.OpenConsole.Info,
            request.OpenConsole.HostRevision,
            request.OpenConsole.Parsing,
            request.OpenConsole.HostExitCodeRoles,
            request.OpenConsole.GlobalOptions,
            request.OpenConsole.Commands,
            request.OpenConsole.Help,
            request.OpenConsole.Completion,
            request.OpenConsole.Compatibility,
            new OpenConsoleProvenance(
                Dummy("shell"),
                request.OpenConsole.GeneratorRevision,
                request.OpenConsole.OperationRevisions));
        var openResult = openConsoleValidator.Validate(document);
        if (!openResult.IsValid)
        {
            throw new ConsoleRequestScaffoldingException(
                openResult.Diagnostics[0].Message,
                openResult.Diagnostics[0].Path);
        }

        if (!DotNetConsoleProjectionValidator.IsExactAlpha2(
                host,
                request.OpenConsole.Commands))
        {
            throw new ConsoleRequestScaffoldingException(
                "The derived schema sets do not exactly match the selected shell host.",
                "/request/openConsole/commands");
        }

        DotNetConsoleBindingDocument binding = new(
            request.Binding.Schema,
            request.Binding.Version,
            Dummy("open-console"),
            new DotNetConsoleConsumerProject(
                request.ConsumerProjectIdentity,
                project.AssemblyName,
                request.ConsumerProjectPath,
                project.TargetFramework,
                string.Concat(project.AssemblyName, ".dll"),
                string.Concat(
                    "obj/",
                    request.Configuration,
                    "/net10.0/ref/",
                    project.AssemblyName,
                    ".dll"),
                new Sha256Digest(
                    "sha256:0000000000000000000000000000000000000000000000000000000000000000")),
            request.Binding.FeatureType,
            request.Binding.ValidationResultType,
            request.Binding.Operations);
        var bindingResult = bindingValidator.Validate(
            binding,
            document.ToVersion1());
        if (!bindingResult.IsValid)
        {
            throw new ConsoleRequestScaffoldingException(
                bindingResult.Diagnostics[0].Message,
                bindingResult.Diagnostics[0].Path);
        }
    }

    private async ValueTask PromoteAsync(
        ConsoleRequestScaffoldPaths paths,
        byte[] bytes,
        CancellationToken cancellationToken)
    {
        try
        {
            await fileSystem.WriteAllBytesAsync(
                paths.StagePath,
                bytes,
                cancellationToken).ConfigureAwait(false);
            var staged = await fileSystem.ReadAllBytesAsync(
                paths.StagePath,
                cancellationToken).ConfigureAwait(false);
            _ = Read<DotNetConsoleInputMaterializationRequestAlpha2>(
                staged,
                "/request");
            ValidateSchema(staged, RequestSchema);
            fileSystem.MoveFile(
                paths.StagePath,
                paths.OutputPath,
                overwrite: false);
        }
        catch (Exception exception)
        {
            if (fileSystem.FileExists(paths.StagePath))
            {
                fileSystem.DeleteFile(paths.StagePath);
            }

            if (exception is ConsoleRequestScaffoldingException or
                OperationCanceledException)
            {
                throw;
            }

            if (exception is ArgumentException or
                IOException or
                InvalidDataException or
                UnauthorizedAccessException)
            {
                throw new ConsoleRequestScaffoldingException(
                    exception.Message,
                    "/output");
            }

            throw;
        }
    }

    private static void ValidateNoPlaceholders(ReadOnlyMemory<byte> bytes)
    {
        try
        {
            Utf8JsonReader reader = new(bytes.Span);
            if (!reader.Read())
            {
                throw new JsonException(
                    "The Console command sketch cannot be empty.");
            }

            VisitJsonValue(ref reader, "");
            if (reader.Read())
            {
                throw new JsonException(
                    "The Console command sketch must contain one JSON value.");
            }
        }
        catch (ConsoleRequestScaffoldingException)
        {
            throw;
        }
        catch (JsonException exception)
        {
            throw new ConsoleRequestScaffoldingException(
                exception.Message,
                exception.Path ?? "/sketch");
        }
    }

    private static void VisitJsonValue(
        ref Utf8JsonReader reader,
        string path)
    {
        switch (reader.TokenType)
        {
            case JsonTokenType.StartObject:
                while (reader.Read() &&
                       reader.TokenType != JsonTokenType.EndObject)
                {
                    if (reader.TokenType != JsonTokenType.PropertyName)
                    {
                        throw new JsonException(
                            "An object member name was expected.");
                    }

                    var name = reader.GetString() ??
                        throw new JsonException(
                            "An object member name cannot be null.");
                    if (!reader.Read())
                    {
                        throw new JsonException(
                            "An object member value was expected.");
                    }

                    VisitJsonValue(
                        ref reader,
                        string.Concat(path, "/", EscapePointer(name)));
                }

                break;
            case JsonTokenType.StartArray:
                var index = 0;
                while (reader.Read() &&
                       reader.TokenType != JsonTokenType.EndArray)
                {
                    VisitJsonValue(
                        ref reader,
                        string.Concat(path, "/", index));
                    index++;
                }

                break;
            case JsonTokenType.String:
                var value = reader.GetString() ?? "";
                if (value.Contains("${", StringComparison.Ordinal) ||
                    value.Contains(
                        "<placeholder>",
                        StringComparison.OrdinalIgnoreCase) ||
                    value.Contains(
                        "TODO",
                        StringComparison.OrdinalIgnoreCase))
                {
                    throw new ConsoleRequestScaffoldingException(
                        "Console command sketches cannot contain unresolved placeholders.",
                        path);
                }

                break;
        }
    }

    private static string EscapePointer(string value) =>
        value.Replace("~", "~0", StringComparison.Ordinal)
            .Replace("/", "~1", StringComparison.Ordinal);

    private static ImmutableArray<ArtifactReference> Sort(
        ImmutableArray<ArtifactReference> values) =>
        values.OrderBy(Exact, StringComparer.Ordinal).ToImmutableArray();

    private static bool HasDuplicates(IEnumerable<string> values)
    {
        HashSet<string> unique = new(StringComparer.Ordinal);
        return values.Any(value => !unique.Add(value));
    }

    private static bool ExactSet(
        IEnumerable<string> first,
        IEnumerable<string> second) =>
        first.ToHashSet(StringComparer.Ordinal)
            .SetEquals(second);

    private static ArtifactReference Dummy(string kind) =>
        new(
            new ProgramKitIdentifier(
                string.Concat("pkid:", kind, ":program-kit:scaffold-preflight")),
            new SemanticVersion("0.1.0-alpha.1"),
            new Sha256Digest(
                "sha256:0000000000000000000000000000000000000000000000000000000000000000"));

    private static ImmutableArray<string> Values(
        XDocument document,
        string localName) =>
        document.Descendants()
            .Where(element =>
                string.Equals(
                    element.Name.LocalName,
                    localName,
                    StringComparison.Ordinal))
            .Select(static element => element.Value.Trim())
            .Where(static value => value.Length > 0)
            .Distinct(StringComparer.Ordinal)
            .ToImmutableArray();

    private static string Exact(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

}
