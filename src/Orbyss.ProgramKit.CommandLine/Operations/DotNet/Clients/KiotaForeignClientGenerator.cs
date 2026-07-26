using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Processes;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>
/// Staged local-only C# client generation through one exact Kiota tool revision.
/// </summary>
public sealed class KiotaForeignClientGenerator : IKiotaForeignClientGenerator
{
    private const string LockPath = "kiota-lock.json";
    private const string ProvenancePath = "program-kit.client-generation.json";
    private const string StagedDescriptionLocation = "../input/openapi.json";

    private static readonly ImmutableArray<string> Serializers =
    [
        "Microsoft.Kiota.Serialization.Json.JsonSerializationWriterFactory",
        "Microsoft.Kiota.Serialization.Text.TextSerializationWriterFactory",
        "Microsoft.Kiota.Serialization.Form.FormSerializationWriterFactory",
        "Microsoft.Kiota.Serialization.Multipart.MultipartSerializationWriterFactory",
    ];

    private static readonly ImmutableArray<string> Deserializers =
    [
        "Microsoft.Kiota.Serialization.Json.JsonParseNodeFactory",
        "Microsoft.Kiota.Serialization.Text.TextParseNodeFactory",
        "Microsoft.Kiota.Serialization.Form.FormParseNodeFactory",
    ];

    private static readonly ImmutableArray<string> StructuredMimeTypes =
    [
        "application/json",
        "text/plain;q=0.9",
        "application/x-www-form-urlencoded;q=0.2",
        "multipart/form-data;q=0.1",
    ];

    private static readonly ImmutableArray<KiotaRuntimeDependency>
        RuntimeDependencies =
        [
            new("Microsoft.Kiota.Abstractions", "2.0.0", "abstractions"),
            new("Microsoft.Kiota.Http.HttpClientLibrary", "2.0.0", "http"),
            new("Microsoft.Kiota.Serialization.Form", "2.0.0", "serialization"),
            new("Microsoft.Kiota.Serialization.Json", "2.0.0", "serialization"),
            new("Microsoft.Kiota.Authentication.Azure", "2.0.0", "authentication"),
            new("Microsoft.Kiota.Serialization.Text", "2.0.0", "serialization"),
            new("Microsoft.Kiota.Serialization.Multipart", "2.0.0", "serialization"),
            new("Microsoft.Kiota.Bundle", "2.0.0", "bundle"),
        ];

    private readonly ICommandFileSystem fileSystem;
    private readonly ICommandProcessRunner processRunner;
    private readonly IKiotaToolPackageMaterializer toolMaterializer;

    /// <summary>Initializes exact filesystem and process boundaries.</summary>
    public KiotaForeignClientGenerator(
        ICommandFileSystem fileSystem,
        ICommandProcessRunner processRunner,
        IKiotaToolPackageMaterializer toolMaterializer)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.processRunner = processRunner ??
            throw new ArgumentNullException(nameof(processRunner));
        this.toolMaterializer = toolMaterializer ??
            throw new ArgumentNullException(nameof(toolMaterializer));
    }

    /// <inheritdoc />
    public async ValueTask<KiotaForeignClientGenerationResult> GenerateAsync(
        KiotaForeignClientGenerationRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        ValidateIdentifiers(request);
        ValidatePatterns(request.IncludePatterns, "/options/includePatterns");
        ValidatePatterns(request.ExcludePatterns, "/options/excludePatterns");

        var inputPath = Path.GetFullPath(request.OpenApiPath);
        var manifestPath = Path.GetFullPath(request.ToolManifestPath);
        var outputRoot = Path.GetFullPath(request.OutputRoot);
        if (!fileSystem.FileExists(inputPath))
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.InvalidInput,
                "The explicit local OpenAPI JSON file does not exist.",
                "/input");
        }

        if (!fileSystem.FileExists(manifestPath))
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.InvalidToolManifest,
                "The explicit Kiota tool manifest does not exist.",
                "/toolManifest");
        }

        try
        {
            LocalOperationPaths.EnsureSafeRoot(outputRoot);
            LocalOperationPaths.EnsureOutputAbsent(outputRoot);
        }
        catch (Exception exception) when (
            exception is InvalidDataException or IOException)
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.UnsafeOutput,
                exception.Message,
                "/output");
        }

        var input = await fileSystem.ReadAllBytesAsync(
            inputPath,
            cancellationToken).ConfigureAwait(false);
        ValidateLocalJsonOpenApi(input.Span);
        var inputDigest = LocalOperationHashes.Sha256(input.Span);
        await ValidateManifestAsync(
            manifestPath,
            cancellationToken).ConfigureAwait(false);

        var outputParent = Path.GetDirectoryName(outputRoot) ??
            throw Failure(
                KiotaGenerationDiagnosticIds.UnsafeOutput,
                "The explicit output has no parent directory.",
                "/output");
        fileSystem.CreateDirectory(outputParent);
        var workRoot = Path.Combine(
            outputParent,
            string.Concat(
                ".program-kit-kiota-",
                Guid.NewGuid().ToString("N")));
        try
        {
            LocalOperationPaths.EnsureOutputAbsent(workRoot);
            fileSystem.CreateDirectory(workRoot);
            var stagedInput = Path.Combine(workRoot, "input", "openapi.json");
            await fileSystem.WriteAllBytesAsync(
                stagedInput,
                input,
                cancellationToken).ConfigureAwait(false);
            var toolEntry = await toolMaterializer.MaterializeAsync(
                request.ToolPackagePath,
                Path.Combine(workRoot, "tool"),
                cancellationToken).ConfigureAwait(false);
            await VerifyToolAsync(
                toolEntry,
                workRoot,
                cancellationToken).ConfigureAwait(false);

            var generatedRoot = Path.Combine(workRoot, "client");
            var result = await processRunner.RunAsync(
                new CommandProcessRequest(
                    "dotnet",
                    workRoot,
                    GenerationArguments(
                        toolEntry,
                        stagedInput,
                        generatedRoot,
                        request),
                    IsolatedEnvironment(workRoot)),
                cancellationToken).ConfigureAwait(false);
            if (result.ExitCode != 0)
            {
                throw Failure(
                    KiotaGenerationDiagnosticIds.ToolFailure,
                    ContainedProcessMessage(
                        "Pinned Kiota client generation failed.",
                        result),
                    "/generation");
            }

            var lockFilePath = Path.Combine(generatedRoot, LockPath);
            if (!fileSystem.FileExists(lockFilePath))
            {
                throw Failure(
                    KiotaGenerationDiagnosticIds.LockMismatch,
                    "Pinned Kiota generation emitted no lock file.",
                    "/output/kiota-lock.json");
            }

            var lockBytes = await fileSystem.ReadAllBytesAsync(
                lockFilePath,
                cancellationToken).ConfigureAwait(false);
            ValidateLock(lockBytes.Span, request);
            var lockDigest = LocalOperationHashes.Sha256(lockBytes.Span);
            var generatedFiles = await HashGeneratedFilesAsync(
                generatedRoot,
                cancellationToken).ConfigureAwait(false);
            var generatedSourceTreeDigest = HashTree(generatedFiles);
            await fileSystem.WriteAllBytesAsync(
                Path.Combine(generatedRoot, ProvenancePath),
                RenderProvenance(
                    inputDigest,
                    lockDigest,
                    generatedSourceTreeDigest,
                    request),
                cancellationToken).ConfigureAwait(false);
            var files = await HashGeneratedFilesAsync(
                generatedRoot,
                cancellationToken).ConfigureAwait(false);
            var treeDigest = HashTree(files);
            fileSystem.MoveDirectory(generatedRoot, outputRoot);
            fileSystem.DeleteDirectory(workRoot);
            return new KiotaForeignClientGenerationResult(
                outputRoot,
                inputDigest,
                lockDigest,
                treeDigest,
                files,
                RuntimeDependencies);
        }
        catch
        {
            fileSystem.DeleteDirectory(workRoot);
            throw;
        }
    }

    private async ValueTask ValidateManifestAsync(
        string manifestPath,
        CancellationToken cancellationToken)
    {
        var bytes = await fileSystem.ReadAllBytesAsync(
            manifestPath,
            cancellationToken).ConfigureAwait(false);
        if (!string.Equals(
                LocalOperationHashes.Sha256(bytes.Span).Value,
                KiotaToolSelection.ManifestDigest,
                StringComparison.Ordinal))
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.InvalidToolManifest,
                "The Kiota tool manifest bytes differ from the reviewed selection.",
                "/toolManifest");
        }
    }

    private async ValueTask VerifyToolAsync(
        string toolEntry,
        string workRoot,
        CancellationToken cancellationToken)
    {
        var result = await processRunner.RunAsync(
            new CommandProcessRequest(
                "dotnet",
                workRoot,
                [
                    toolEntry,
                    "--version",
                ],
                IsolatedEnvironment(workRoot)),
            cancellationToken).ConfigureAwait(false);
        if (result.ExitCode != 0 ||
            !string.Equals(
                result.StandardOutput.Trim(),
                KiotaToolSelection.ToolVersionEvidence,
                StringComparison.Ordinal))
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.ToolFailure,
                ContainedProcessMessage(
                    "The resolved Kiota command does not match the exact reviewed version.",
                    result),
                "/tool");
        }
    }

    private async ValueTask<ImmutableArray<KiotaGeneratedFile>>
        HashGeneratedFilesAsync(
            string generatedRoot,
            CancellationToken cancellationToken)
    {
        if (!fileSystem.DirectoryExists(generatedRoot))
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.InvalidOutput,
                "Pinned Kiota generation emitted no output directory.",
                "/output");
        }

        var files = ImmutableArray.CreateBuilder<KiotaGeneratedFile>();
        foreach (var path in fileSystem.EnumerateFiles(generatedRoot))
        {
            var relativePath = LocalOperationPaths.RelativeTo(
                generatedRoot,
                path);
            var bytes = await fileSystem.ReadAllBytesAsync(
                path,
                cancellationToken).ConfigureAwait(false);
            files.Add(
                new KiotaGeneratedFile(
                    relativePath,
                    bytes.Length,
                    LocalOperationHashes.Sha256(bytes.Span)));
        }

        if (files.Count < 2 ||
            !files.Any(static file =>
                string.Equals(
                    file.RelativePath,
                    LockPath,
                    StringComparison.Ordinal)) ||
            !files.Any(static file =>
                file.RelativePath.EndsWith(".cs", StringComparison.Ordinal)))
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.InvalidOutput,
                "Pinned Kiota generation emitted an incomplete client tree.",
                "/output");
        }

        return files
            .OrderBy(static file => file.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
    }

    private static Sha256Digest HashTree(
        ImmutableArray<KiotaGeneratedFile> files)
    {
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var file in files)
        {
            hash.AppendData(Encoding.UTF8.GetBytes(file.RelativePath));
            hash.AppendData([0]);
            hash.AppendData(Encoding.UTF8.GetBytes(file.Length.ToString(
                System.Globalization.CultureInfo.InvariantCulture)));
            hash.AppendData([0]);
            hash.AppendData(Encoding.UTF8.GetBytes(file.Digest.Value));
            hash.AppendData([0]);
        }

        return new Sha256Digest(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(hash.GetHashAndReset())));
    }

    private static void ValidateLocalJsonOpenApi(ReadOnlySpan<byte> input)
    {
        try
        {
            Utf8JsonReader reader = new(
                input,
                new JsonReaderOptions
                {
                    AllowTrailingCommas = false,
                    CommentHandling = JsonCommentHandling.Disallow,
                    MaxDepth = 128,
                });
            var sawOpenApi = false;
            var expectsReference = false;
            while (reader.Read())
            {
                if (reader.TokenType == JsonTokenType.PropertyName)
                {
                    var property = reader.GetString();
                    sawOpenApi |= string.Equals(
                        property,
                        "openapi",
                        StringComparison.Ordinal);
                    expectsReference = string.Equals(
                        property,
                        "$ref",
                        StringComparison.Ordinal);
                    continue;
                }

                if (expectsReference)
                {
                    if (reader.TokenType != JsonTokenType.String ||
                        !reader.GetString()!.StartsWith(
                            "#/",
                            StringComparison.Ordinal))
                    {
                        throw Failure(
                            KiotaGenerationDiagnosticIds.InvalidInput,
                            "Only references within the single explicit OpenAPI document are allowed.",
                            "/input/$ref");
                    }

                    expectsReference = false;
                }
            }

            if (!sawOpenApi)
            {
                throw Failure(
                    KiotaGenerationDiagnosticIds.InvalidInput,
                    "The explicit JSON input has no OpenAPI revision.",
                    "/input/openapi");
            }
        }
        catch (JsonException exception)
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.InvalidInput,
                string.Concat("The explicit OpenAPI JSON is invalid: ", exception.Message),
                "/input");
        }
    }

    private static void ValidateLock(
        ReadOnlySpan<byte> lockBytes,
        KiotaForeignClientGenerationRequest request)
    {
        KiotaLockFile? lockFile;
        try
        {
            lockFile = ReadLock(lockBytes);
        }
        catch (JsonException exception)
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.LockMismatch,
                string.Concat("The generated Kiota lock is invalid: ", exception.Message),
                "/output/kiota-lock.json");
        }

        if (lockFile is null ||
            !string.Equals(
                lockFile.KiotaVersion,
                KiotaToolSelection.ToolVersion,
                StringComparison.Ordinal) ||
            !IsSha512(lockFile.DescriptionHash) ||
            !string.Equals(lockFile.LockFileVersion, "1.0.0", StringComparison.Ordinal) ||
            !string.Equals(lockFile.DescriptionLocation, StagedDescriptionLocation, StringComparison.Ordinal) ||
            !string.Equals(lockFile.ClientClassName, request.ClassName, StringComparison.Ordinal) ||
            !string.Equals(lockFile.ClientNamespaceName, request.NamespaceName, StringComparison.Ordinal) ||
            !string.Equals(lockFile.Language, "CSharp", StringComparison.Ordinal) ||
            !string.Equals(lockFile.TypeAccessModifier, "Public", StringComparison.Ordinal) ||
            lockFile.UsesBackingStore ||
            !lockFile.ExcludeBackwardCompatible ||
            !lockFile.IncludeAdditionalData ||
            lockFile.DisableSslValidation ||
            !lockFile.Serializers.SequenceEqual(Serializers) ||
            !lockFile.Deserializers.SequenceEqual(Deserializers) ||
            !lockFile.StructuredMimeTypes.SequenceEqual(StructuredMimeTypes) ||
            !lockFile.IncludePatterns.SequenceEqual(request.IncludePatterns) ||
            !lockFile.ExcludePatterns.SequenceEqual(request.ExcludePatterns) ||
            !lockFile.DisabledValidationRules.IsEmpty ||
            !lockFile.AllowedExternalOrigins.IsEmpty)
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.LockMismatch,
                "The generated Kiota lock differs from the exact reviewed input and options.",
                "/output/kiota-lock.json");
        }
    }

    private static KiotaLockFile ReadLock(ReadOnlySpan<byte> lockBytes)
    {
        Utf8JsonReader reader = new(
            lockBytes,
            new JsonReaderOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
                MaxDepth = 16,
            });
        if (!reader.Read() || reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException("The Kiota lock root must be an object.");
        }

        string? descriptionHash = null;
        string? descriptionLocation = null;
        string? lockFileVersion = null;
        string? kiotaVersion = null;
        string? clientClassName = null;
        string? typeAccessModifier = null;
        string? clientNamespaceName = null;
        string? language = null;
        bool? usesBackingStore = null;
        bool? excludeBackwardCompatible = null;
        bool? includeAdditionalData = null;
        bool? disableSslValidation = null;
        ImmutableArray<string> serializers = default;
        ImmutableArray<string> deserializers = default;
        ImmutableArray<string> structuredMimeTypes = default;
        ImmutableArray<string> includePatterns = default;
        ImmutableArray<string> excludePatterns = default;
        ImmutableArray<string> disabledValidationRules = default;
        ImmutableArray<string> allowedExternalOrigins = default;
        HashSet<string> seen = new(StringComparer.Ordinal);
        var sawEndObject = false;
        while (reader.Read())
        {
            if (reader.TokenType == JsonTokenType.EndObject)
            {
                sawEndObject = true;
                break;
            }

            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException(
                    "The Kiota lock contains an invalid object member.");
            }

            var property = reader.GetString() ??
                throw new JsonException(
                    "The Kiota lock contains an invalid property name.");
            if (!seen.Add(property))
            {
                throw new JsonException(
                    "The Kiota lock contains a duplicate property.");
            }

            if (!reader.Read())
            {
                throw new JsonException(
                    "The Kiota lock property has no value.");
            }

            switch (property)
            {
                case "descriptionHash":
                    descriptionHash = ReadString(ref reader);
                    break;
                case "descriptionLocation":
                    descriptionLocation = ReadString(ref reader);
                    break;
                case "lockFileVersion":
                    lockFileVersion = ReadString(ref reader);
                    break;
                case "kiotaVersion":
                    kiotaVersion = ReadString(ref reader);
                    break;
                case "clientClassName":
                    clientClassName = ReadString(ref reader);
                    break;
                case "typeAccessModifier":
                    typeAccessModifier = ReadString(ref reader);
                    break;
                case "clientNamespaceName":
                    clientNamespaceName = ReadString(ref reader);
                    break;
                case "language":
                    language = ReadString(ref reader);
                    break;
                case "usesBackingStore":
                    usesBackingStore = ReadBoolean(ref reader);
                    break;
                case "excludeBackwardCompatible":
                    excludeBackwardCompatible = ReadBoolean(ref reader);
                    break;
                case "includeAdditionalData":
                    includeAdditionalData = ReadBoolean(ref reader);
                    break;
                case "disableSSLValidation":
                    disableSslValidation = ReadBoolean(ref reader);
                    break;
                case "serializers":
                    serializers = ReadStringArray(ref reader);
                    break;
                case "deserializers":
                    deserializers = ReadStringArray(ref reader);
                    break;
                case "structuredMimeTypes":
                    structuredMimeTypes = ReadStringArray(ref reader);
                    break;
                case "includePatterns":
                    includePatterns = ReadStringArray(ref reader);
                    break;
                case "excludePatterns":
                    excludePatterns = ReadStringArray(ref reader);
                    break;
                case "disabledValidationRules":
                    disabledValidationRules = ReadStringArray(ref reader);
                    break;
                case "allowedExternalOrigins":
                    allowedExternalOrigins = ReadStringArray(ref reader);
                    break;
                default:
                    throw new JsonException(
                        "The Kiota lock contains an unreviewed property.");
            }
        }

        if (!sawEndObject || reader.Read() || seen.Count != 19)
        {
            throw new JsonException(
                "The Kiota lock has missing, incomplete, or trailing JSON content.");
        }

        return new KiotaLockFile(
            descriptionHash ?? string.Empty,
            descriptionLocation ?? string.Empty,
            lockFileVersion ?? string.Empty,
            kiotaVersion ?? string.Empty,
            clientClassName ?? string.Empty,
            typeAccessModifier ?? string.Empty,
            clientNamespaceName ?? string.Empty,
            language ?? string.Empty,
            usesBackingStore ?? false,
            excludeBackwardCompatible ?? false,
            includeAdditionalData ?? false,
            disableSslValidation ?? false,
            serializers,
            deserializers,
            structuredMimeTypes,
            includePatterns,
            excludePatterns,
            disabledValidationRules,
            allowedExternalOrigins);
    }

    private static string ReadString(ref Utf8JsonReader reader) =>
        reader.TokenType == JsonTokenType.String
            ? reader.GetString()!
            : throw new JsonException(
                "The Kiota lock property must be a string.");

    private static bool ReadBoolean(ref Utf8JsonReader reader) =>
        reader.TokenType switch
        {
            JsonTokenType.True => true,
            JsonTokenType.False => false,
            _ => throw new JsonException(
                "The Kiota lock property must be a boolean."),
        };

    private static ImmutableArray<string> ReadStringArray(
        ref Utf8JsonReader reader)
    {
        if (reader.TokenType != JsonTokenType.StartArray)
        {
            throw new JsonException(
                "The Kiota lock property must be a string array.");
        }

        var values = ImmutableArray.CreateBuilder<string>();
        while (reader.Read() && reader.TokenType != JsonTokenType.EndArray)
        {
            values.Add(ReadString(ref reader));
        }

        if (reader.TokenType != JsonTokenType.EndArray)
        {
            throw new JsonException(
                "The Kiota lock string array is incomplete.");
        }

        return values.ToImmutable();
    }

    private static ImmutableArray<string> GenerationArguments(
        string toolEntry,
        string stagedInput,
        string outputRoot,
        KiotaForeignClientGenerationRequest request)
    {
        var arguments = ImmutableArray.CreateBuilder<string>();
        foreach (var argument in new[]
                 {
                     toolEntry,
                     "generate",
                     "--openapi",
                     stagedInput,
                     "--language",
                     "CSharp",
                     "--namespace-name",
                     request.NamespaceName,
                     "--class-name",
                     request.ClassName,
                     "--output",
                     outputRoot,
                     "--clean-output",
                     "--exclude-backward-compatible",
                     "--log-level",
                     "error",
                 })
        {
            arguments.Add(argument);
        }
        foreach (var pattern in request.IncludePatterns)
        {
            arguments.Add("--include-path");
            arguments.Add(pattern);
        }

        foreach (var pattern in request.ExcludePatterns)
        {
            arguments.Add("--exclude-path");
            arguments.Add(pattern);
        }

        return arguments.ToImmutable();
    }

    private static ReadOnlyMemory<byte> RenderProvenance(
        Sha256Digest inputDigest,
        Sha256Digest lockDigest,
        Sha256Digest generatedSourceTreeDigest,
        KiotaForeignClientGenerationRequest request)
    {
        using MemoryStream stream = new();
        using (Utf8JsonWriter writer = new(
                   stream,
                   new JsonWriterOptions
                   {
                       Indented = true,
                   }))
        {
            writer.WriteStartObject();
            writer.WriteString(
                "schema",
                "pkid:schema:program-kit:kiota-foreign-client-provenance@1.0.0");
            writer.WriteString("inputOwnership", "foreign");
            writer.WriteString("inputSha256", inputDigest.Value);
            writer.WriteStartObject("tool");
            writer.WriteString("package", "Microsoft.OpenApi.Kiota");
            writer.WriteString("version", KiotaToolSelection.ToolVersion);
            writer.WriteString(
                "versionEvidence",
                KiotaToolSelection.ToolVersionEvidence);
            writer.WriteString(
                "sourceCommit",
                KiotaToolSelection.SourceCommit);
            writer.WriteString(
                "manifestSha256",
                KiotaToolSelection.ManifestDigest);
            writer.WriteString(
                "packageSha256",
                KiotaToolSelection.PackageDigest);
            writer.WriteString(
                "entryAssemblySha256",
                KiotaToolSelection.EntryDigest);
            writer.WriteEndObject();
            writer.WriteStartObject("options");
            writer.WriteString("language", "CSharp");
            writer.WriteString("namespace", request.NamespaceName);
            writer.WriteString("className", request.ClassName);
            WriteArray(writer, "includePatterns", request.IncludePatterns);
            WriteArray(writer, "excludePatterns", request.ExcludePatterns);
            writer.WriteBoolean("cleanOutput", true);
            writer.WriteBoolean("excludeBackwardCompatible", true);
            writer.WriteEndObject();
            writer.WriteString("lockSha256", lockDigest.Value);
            writer.WriteString(
                "generatedSourceTreeSha256",
                generatedSourceTreeDigest.Value);
            writer.WriteStartArray("runtimeDependencies");
            foreach (var dependency in RuntimeDependencies)
            {
                writer.WriteStartObject();
                writer.WriteString("package", dependency.Package);
                writer.WriteString("version", dependency.Version);
                writer.WriteString("kind", dependency.Kind);
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteEndObject();
        }

        var content = stream.ToArray();
        var withNewLine = new byte[content.Length + 1];
        content.CopyTo(withNewLine, 0);
        withNewLine[^1] = (byte)'\n';
        return withNewLine;
    }

    private static void WriteArray(
        Utf8JsonWriter writer,
        string name,
        ImmutableArray<string> values)
    {
        writer.WriteStartArray(name);
        foreach (var value in values)
        {
            writer.WriteStringValue(value);
        }

        writer.WriteEndArray();
    }

    private static bool IsSha512(string value) =>
        value.Length == 128 &&
        value.All(static character =>
            character is >= '0' and <= '9' or >= 'A' and <= 'F');

    private static ImmutableDictionary<string, string> IsolatedEnvironment(
        string workRoot) =>
        ImmutableDictionary<string, string>.Empty
            .Add("APPDATA", Path.Combine(workRoot, "application-data"))
            .Add("DOTNET_CLI_HOME", Path.Combine(workRoot, "dotnet-home"))
            .Add("DOTNET_CLI_TELEMETRY_OPTOUT", "1")
            .Add("DOTNET_NOLOGO", "1")
            .Add("LOCALAPPDATA", Path.Combine(workRoot, "local-application-data"))
            .Add("TEMP", Path.Combine(workRoot, "temporary"))
            .Add("TMP", Path.Combine(workRoot, "temporary"));

    private static void ValidateIdentifiers(
        KiotaForeignClientGenerationRequest request)
    {
        if (!IsIdentifier(request.ClassName) ||
            request.NamespaceName.Split('.').Any(static part =>
                !IsIdentifier(part)))
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.InvalidInput,
                "The C# namespace and client class must be explicit identifiers.",
                "/options");
        }
    }

    private static bool IsIdentifier(string value) =>
        !string.IsNullOrWhiteSpace(value) &&
        (char.IsAsciiLetter(value[0]) || value[0] == '_') &&
        value.Skip(1).All(static character =>
            char.IsAsciiLetterOrDigit(character) || character == '_');

    private static void ValidatePatterns(
        ImmutableArray<string> patterns,
        string path)
    {
        if (patterns.IsDefault ||
            patterns.Any(static pattern =>
                string.IsNullOrWhiteSpace(pattern) ||
                pattern.Contains('\r', StringComparison.Ordinal) ||
                pattern.Contains('\n', StringComparison.Ordinal)))
        {
            throw Failure(
                KiotaGenerationDiagnosticIds.InvalidInput,
                "Kiota path filters must be explicit non-empty single-line values.",
                path);
        }
    }

    private static string ContainedProcessMessage(
        string message,
        CommandProcessResult result)
    {
        var detail = string.Concat(
            result.StandardError,
            Environment.NewLine,
            result.StandardOutput).Trim();
        return detail.Length == 0
            ? message
            : string.Concat(
                message,
                " ",
                detail[..Math.Min(detail.Length, 2048)]);
    }

    private static KiotaGenerationException Failure(
        string diagnosticId,
        string message,
        string path) =>
        new(diagnosticId, message, path);
}
