using System.Security.Cryptography;
using Orbyss.ProgramKit.CommandLine.Operations.Processes;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Clients;

internal sealed class RecordingKiotaRunner(
    bool failGeneration = false,
    bool cancelGeneration = false,
    bool omitLock = false) :
    ICommandProcessRunner
{
    internal List<CommandProcessRequest> Requests { get; } = [];

    public async ValueTask<CommandProcessResult> RunAsync(
        CommandProcessRequest request,
        CancellationToken cancellationToken)
    {
        Requests.Add(request);
        if (!request.Arguments.Contains("generate"))
        {
            return new CommandProcessResult(
                0,
                "1.34.1+9f9cfb3b1cb9b5311a214ea6ce0f69943c523005",
                string.Empty);
        }

        var output = Argument(request, "--output");
        Directory.CreateDirectory(output);
        var namespaceName = Argument(request, "--namespace-name");
        var className = Argument(request, "--class-name");
        await File.WriteAllTextAsync(
            Path.Combine(output, string.Concat(className, ".cs")),
            string.Concat(
                "namespace ",
                namespaceName,
                ";\npublic sealed class ",
                className,
                " { }\n"),
            cancellationToken);
        if (failGeneration)
        {
            return new CommandProcessResult(1, string.Empty, "failed");
        }

        if (cancelGeneration)
        {
            throw new OperationCanceledException(
                "The recording Kiota generation was cancelled.");
        }

        if (omitLock)
        {
            return new CommandProcessResult(0, "partial", string.Empty);
        }

        var input = Argument(request, "--openapi");
        var descriptionHash = Convert.ToHexString(
            SHA512.HashData(await File.ReadAllBytesAsync(
                input,
                cancellationToken)));
        await File.WriteAllTextAsync(
            Path.Combine(output, "kiota-lock.json"),
            Lock(descriptionHash, namespaceName, className),
            cancellationToken);
        return new CommandProcessResult(0, "generated", string.Empty);
    }

    private static string Argument(
        CommandProcessRequest request,
        string name)
    {
        var index = request.Arguments.IndexOf(name);
        Assert.IsGreaterThanOrEqualTo(0, index);
        return request.Arguments[index + 1];
    }

    private static string Lock(
        string descriptionHash,
        string namespaceName,
        string className) =>
        $$"""
        {
          "descriptionHash": "{{descriptionHash}}",
          "descriptionLocation": "../input/openapi.json",
          "lockFileVersion": "1.0.0",
          "kiotaVersion": "1.34.1",
          "clientClassName": "{{className}}",
          "typeAccessModifier": "Public",
          "clientNamespaceName": "{{namespaceName}}",
          "language": "CSharp",
          "usesBackingStore": false,
          "excludeBackwardCompatible": true,
          "includeAdditionalData": true,
          "disableSSLValidation": false,
          "serializers": [
            "Microsoft.Kiota.Serialization.Json.JsonSerializationWriterFactory",
            "Microsoft.Kiota.Serialization.Text.TextSerializationWriterFactory",
            "Microsoft.Kiota.Serialization.Form.FormSerializationWriterFactory",
            "Microsoft.Kiota.Serialization.Multipart.MultipartSerializationWriterFactory"
          ],
          "deserializers": [
            "Microsoft.Kiota.Serialization.Json.JsonParseNodeFactory",
            "Microsoft.Kiota.Serialization.Text.TextParseNodeFactory",
            "Microsoft.Kiota.Serialization.Form.FormParseNodeFactory"
          ],
          "structuredMimeTypes": [
            "application/json",
            "text/plain;q=0.9",
            "application/x-www-form-urlencoded;q=0.2",
            "multipart/form-data;q=0.1"
          ],
          "includePatterns": [],
          "excludePatterns": [],
          "disabledValidationRules": [],
          "allowedExternalOrigins": []
        }
        """;
}
