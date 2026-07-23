using System.Globalization;
using System.Collections;
using System.Reflection;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Diagnostics;

namespace Orbyss.ProgramKit.Workbench.Operations.Schemas;

/// <summary>JsonSchema.Net adapter kept internal to the Workbench model boundary.</summary>
public sealed class JsonSchemaWorkbenchValidator : IWorkbenchSchemaValidator
{
    private readonly IProgramKitJsonCanonicalizer canonicalizer;
    private readonly IProgramKitSemanticValidator<IProgramKitSchemaModule> moduleValidator;

    /// <summary>Initializes schema validation with bounded canonical parsing.</summary>
    public JsonSchemaWorkbenchValidator(
        IProgramKitJsonCanonicalizer canonicalizer,
        IProgramKitSemanticValidator<IProgramKitSchemaModule> moduleValidator)
    {
        this.canonicalizer = canonicalizer ?? throw new ArgumentNullException(nameof(canonicalizer));
        this.moduleValidator = moduleValidator ?? throw new ArgumentNullException(nameof(moduleValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        ReadOnlyMemory<byte> utf8Json,
        IProgramKitSchemaModule schemaModule,
        ArtifactReference schemaReference,
        JsonSerializationLimits limits)
    {
        ArgumentNullException.ThrowIfNull(schemaModule);
        ArgumentNullException.ThrowIfNull(schemaReference);
        ArgumentNullException.ThrowIfNull(limits);

        var moduleValidation = moduleValidator.Validate(schemaModule);
        if (!moduleValidation.IsValid)
        {
            return moduleValidation;
        }

        var resource = schemaModule.Resources.FirstOrDefault(candidate =>
            candidate.SchemaReference == schemaReference);
        if (resource is null)
        {
            return ProgramKitValidationResult.From(
            [
                WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.SchemaValidationFailed,
                    "The exact schema reference is not registered by the supplied module.",
                    "/schemaReference"),
            ]);
        }

        try
        {
            var canonicalInstance = canonicalizer.Canonicalize(utf8Json.Span, limits);
            var schemaBytes = ReadBounded(schemaModule.OpenRead(schemaReference), limits.MaxUtf8Bytes);
            var schemaDigest = Digest(schemaBytes);
            if (schemaDigest != schemaReference.Digest)
            {
                return ProgramKitValidationResult.From(
                [
                    WorkbenchDiagnostics.Error(
                        WorkbenchDiagnosticIds.SchemaValidationFailed,
                        "The opened schema bytes do not match the selected exact digest.",
                        "/schemaReference/digest"),
                ]);
            }

            var engine = JsonSchemaNetReflection.Create();
            foreach (var registeredResource in schemaModule.Resources.OrderBy(
                         static candidate => candidate.CanonicalUri.AbsoluteUri,
                         StringComparer.Ordinal))
            {
                var bytes = ReadBounded(
                    schemaModule.OpenRead(registeredResource.SchemaReference),
                    limits.MaxUtf8Bytes);
                if (Digest(bytes) != registeredResource.SchemaReference.Digest)
                {
                    throw new InvalidDataException(
                        "A registered schema resource does not match its exact digest.");
                }

                engine.Register(
                    registeredResource.CanonicalUri,
                    Encoding.UTF8.GetString(bytes));
            }

            using var instance = JsonDocument.Parse(canonicalInstance.ToArray());
            var results = engine.Evaluate(
                resource.CanonicalUri,
                instance.RootElement,
                CultureInfo.InvariantCulture);
            if (results.IsValid)
            {
                return ProgramKitValidationResult.Valid;
            }

            return ProgramKitValidationResult.From(
                results.InvalidLocations
                    .Order(StringComparer.Ordinal)
                    .Select(static location => WorkbenchDiagnostics.Error(
                        WorkbenchDiagnosticIds.SchemaValidationFailed,
                        "The JSON value does not conform to the selected schema.",
                        location)));
        }
        catch (Exception exception) when (
            exception is JsonException or InvalidDataException or InvalidOperationException or
                TargetInvocationException or TypeLoadException)
        {
            return ProgramKitValidationResult.From(
            [
                WorkbenchDiagnostics.Error(
                    WorkbenchDiagnosticIds.SchemaValidationFailed,
                    exception.Message,
                    string.Empty),
            ]);
        }
    }

    private static byte[] ReadBounded(Stream source, long maxBytes)
    {
        ArgumentNullException.ThrowIfNull(source);
        using (source)
        {
            var buffer = new byte[81920];
            using var output = new MemoryStream();
            while (true)
            {
                var count = source.Read(buffer, 0, buffer.Length);
                if (count == 0)
                {
                    return output.ToArray();
                }

                if (output.Length + count > maxBytes)
                {
                    throw new InvalidDataException("A schema resource exceeded the declared byte limit.");
                }

                output.Write(buffer, 0, count);
            }
        }
    }

    private static Sha256Digest Digest(ReadOnlySpan<byte> bytes)
    {
        var digest = System.Security.Cryptography.SHA256.HashData(bytes);
        return new Sha256Digest(
            string.Concat("sha256:", Convert.ToHexString(digest).ToLowerInvariant()));
    }
}
