using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;
using Orbyss.ProgramKit.CommandLine.Operations.Schemas;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.CommandLine.Contracts.Product;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;

/// <summary>
/// Loads one exact allow-listed payload from this installed CLI assembly and
/// rejects any source, digest, closure, command, schema, or role drift.
/// </summary>
public sealed class EmbeddedConsumerCapabilityPayload :
    IConsumerCapabilityPayload
{
    private const string ResourcePrefix =
        "Orbyss.ProgramKit.CommandLine.ConsumerPayload.";
    private static readonly UTF8Encoding StrictUtf8 = new(false, true);
    private readonly Dictionary<string, ReadOnlyMemory<byte>> capabilities;
    private readonly Dictionary<string, ReadOnlyMemory<byte>> adapters;
    private readonly Dictionary<string, ReadOnlyMemory<byte>> resources;
    private readonly Dictionary<string, CapabilityKnowledgeClosure> catalog;

    /// <summary>Loads and validates the complete embedded closure.</summary>
    public EmbeddedConsumerCapabilityPayload(
        ICapabilityBundleManifestReader manifestReader,
        IEnumerable<CommandDescriptor> descriptors,
        ISchemaCatalog schemas)
    {
        ArgumentNullException.ThrowIfNull(manifestReader);
        ArgumentNullException.ThrowIfNull(descriptors);
        ArgumentNullException.ThrowIfNull(schemas);
        var manifestBytes = ReadEmbedded("Manifest");
        ManifestSha256 = Digest(manifestBytes.Span);
        Manifest = manifestReader.Read(manifestBytes.Span);
        CapabilityBundleVerifier.ValidateManifest(Manifest);

        capabilities = Manifest.Capabilities.ToDictionary(
            static entry => entry.CapabilityId,
            entry => VerifiedEmbedded(
                string.Concat("Capability.", entry.CapabilityId),
                entry.Sha256),
            StringComparer.Ordinal);
        adapters = Manifest.OptionalProviderAdapters.ToDictionary(
            static entry => string.Concat(entry.Provider, "/", entry.CapabilityId),
            entry => VerifiedEmbedded(
                string.Concat(
                    "Adapter.",
                    entry.Provider,
                    ".",
                    entry.CapabilityId),
                entry.Sha256),
            StringComparer.Ordinal);
        resources = Manifest.SupportingResources.ToDictionary(
            static entry => entry.ResourceId,
            entry => VerifiedEmbedded(
                string.Concat("Resource.", entry.ResourceId),
                entry.Sha256),
            StringComparer.Ordinal);

        var descriptorKeys = descriptors.Select(static item => item.Key)
            .ToHashSet(StringComparer.Ordinal);
        catalog = ReadCatalog(
                ReadResource("consumer-capability-catalog"),
                descriptorKeys,
                schemas)
            .ToDictionary(
                static entry => entry.CapabilityId,
                StringComparer.Ordinal);
        Catalog = catalog.Values
            .OrderBy(static entry => entry.CapabilityId, StringComparer.Ordinal)
            .ToImmutableArray();
        ValidateCompleteClosure();
    }

    /// <inheritdoc />
    public CapabilityBundleManifest Manifest { get; }

    /// <inheritdoc />
    public string ManifestSha256 { get; }

    /// <inheritdoc />
    public ImmutableArray<CapabilityKnowledgeClosure> Catalog { get; }

    /// <inheritdoc />
    public ReadOnlyMemory<byte> ReadCapability(string capabilityId)
    {
        var entry = ResolveCatalogEntry(capabilityId);
        if (!string.Equals(entry.Role, "consumer", StringComparison.Ordinal) ||
            !string.Equals(entry.Availability, "available", StringComparison.Ordinal) ||
            !capabilities.TryGetValue(capabilityId, out var content))
        {
            throw new CommandInvocationException(
                string.Concat(
                    "Capability '",
                    capabilityId,
                    "' is not an available consumer capability. ",
                    entry.Reason),
                "/capability");
        }

        return content;
    }

    /// <inheritdoc />
    public ReadOnlyMemory<byte> ReadAdapter(
        string provider,
        string capabilityId)
    {
        var key = string.Concat(provider, "/", capabilityId);
        if (!adapters.TryGetValue(key, out var content))
        {
            throw new CommandInvocationException(
                string.Concat(
                    "No reviewed adapter is registered for '",
                    key,
                    "'."),
                "/provider");
        }

        return content;
    }

    /// <inheritdoc />
    public ReadOnlyMemory<byte> ReadResource(string resourceId)
    {
        var normalized = ResourceAlias(resourceId);
        if (!resources.TryGetValue(normalized, out var content))
        {
            throw new CommandInvocationException(
                string.Concat(
                    "Supporting resource '",
                    resourceId,
                    "' is not allow-listed. Available IDs: ",
                    string.Join(", ", resources.Keys.Order(StringComparer.Ordinal)),
                    "."),
                "/resource");
        }

        return content;
    }

    /// <inheritdoc />
    public CapabilityKnowledgeClosure ResolveCatalogEntry(string capabilityId)
    {
        if (string.IsNullOrWhiteSpace(capabilityId) ||
            !catalog.TryGetValue(capabilityId, out var entry))
        {
            throw new CommandInvocationException(
                string.Concat(
                    "Capability '",
                    capabilityId,
                    "' is not in this release catalog."),
                "/capability");
        }

        return entry;
    }

    private static string ResourceAlias(string resourceId)
    {
        const string profilePrefix =
            "pkid:completion-profile:program-kit:";
        return resourceId.StartsWith(profilePrefix, StringComparison.Ordinal)
            ? string.Concat(
                "software-change-profile-",
                resourceId[profilePrefix.Length..])
            : resourceId;
    }

    private static ReadOnlyMemory<byte> VerifiedEmbedded(
        string logicalSuffix,
        string expectedDigest)
    {
        var bytes = ReadEmbedded(logicalSuffix);
        if (!string.Equals(
                Digest(bytes.Span),
                expectedDigest,
                StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                string.Concat(
                    "Embedded consumer payload '",
                    logicalSuffix,
                    "' differs from its manifest digest."));
        }

        return bytes;
    }

    private static ReadOnlyMemory<byte> ReadEmbedded(string logicalSuffix)
    {
        using var stream = typeof(EmbeddedConsumerCapabilityPayload)
                .Assembly.GetManifestResourceStream(
                    string.Concat(ResourcePrefix, logicalSuffix))
            ?? throw new InvalidDataException(
                string.Concat(
                    "The embedded consumer payload item '",
                    logicalSuffix,
                    "' is missing."));
        using MemoryStream output = new();
        stream.CopyTo(output);
        return output.ToArray();
    }

    private static ImmutableArray<CapabilityKnowledgeClosure> ReadCatalog(
        ReadOnlyMemory<byte> content,
        HashSet<string> descriptorKeys,
        ISchemaCatalog schemas)
    {
        var document =
            ConsumerCapabilityCatalogSerializer.Read(content.Span);
        RequireString(
            document.FormatVersion,
            "formatVersion",
            ProgramKitProductInfo.CapabilityKnowledgeFormatVersion);
        RequireString(
            document.ProductVersion,
            "productVersion",
            ProgramKitProductInfo.Version);
        var providers = ValidateStrings(document.Providers, "providers");
        if (!providers.SequenceEqual(["claude", "codex"], StringComparer.Ordinal))
        {
            throw new InvalidDataException(
                "The consumer capability catalog provider set is invalid.");
        }

        var builder = ImmutableArray.CreateBuilder<CapabilityKnowledgeClosure>();
        foreach (var value in document.Capabilities)
        {
            var entry = new CapabilityKnowledgeClosure(
                RequiredString(value.CapabilityId, "capabilityId"),
                RequiredString(value.Role, "role"),
                RequiredString(value.Availability, "availability"),
                RequiredString(value.Reason, "reason", allowEmpty: true),
                ValidateStrings(value.Commands, "commands"),
                ValidateStrings(value.Resources, "resources"),
                ValidateStrings(value.Schemas, "schemas"),
                ValidateStrings(value.HumanInputs, "humanInputs"),
                ValidateStrings(value.ExternalInputs, "externalInputs"));
            foreach (var command in entry.Commands)
            {
                if (!descriptorKeys.Contains(command))
                {
                    throw new InvalidDataException(
                        string.Concat(
                            "Capability '",
                            entry.CapabilityId,
                            "' references unregistered command '",
                            command,
                            "'."));
                }
            }

            foreach (var schema in entry.Schemas)
            {
                _ = schemas.Resolve(schema);
            }

            builder.Add(entry);
        }

        var entries = builder.ToImmutable();
        if (entries.GroupBy(static item => item.CapabilityId, StringComparer.Ordinal)
            .Any(static group => group.Count() != 1))
        {
            throw new InvalidDataException(
                "Capability catalog IDs must be unique.");
        }

        return entries;
    }

    private void ValidateCompleteClosure()
    {
        var available = Catalog.Where(
                static entry =>
                    string.Equals(entry.Role, "consumer", StringComparison.Ordinal) &&
                    string.Equals(entry.Availability, "available", StringComparison.Ordinal))
            .Select(static entry => entry.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var manifested = Manifest.Capabilities
            .Select(static entry => entry.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!available.SequenceEqual(manifested, StringComparer.Ordinal))
        {
            throw new InvalidDataException(
                "Every and only available consumer capabilities must be manifested.");
        }

        foreach (var entry in Catalog)
        {
            if (!string.Equals(entry.Availability, "available", StringComparison.Ordinal))
            {
                if (!entry.Commands.IsDefaultOrEmpty ||
                    !entry.Resources.IsDefaultOrEmpty ||
                    !entry.Schemas.IsDefaultOrEmpty ||
                    string.IsNullOrWhiteSpace(entry.Reason))
                {
                    throw new InvalidDataException(
                        "Unavailable catalog entries must have a reason and no retrievable closure.");
                }

                continue;
            }

            if (!capabilities.TryGetValue(entry.CapabilityId, out var definition))
            {
                throw new InvalidDataException(
                    "An available capability definition is missing.");
            }

            var markdown = StrictUtf8.GetString(definition.Span);
            if (markdown.Contains(".agent-capabilities/", StringComparison.Ordinal) ||
                markdown.Contains("../", StringComparison.Ordinal))
            {
                throw new InvalidDataException(
                    string.Concat(
                        "Consumer capability '",
                        entry.CapabilityId,
                        "' contains a source-relative knowledge pointer."));
            }

            foreach (var resource in entry.Resources)
            {
                _ = ReadResource(resource);
            }

            foreach (var provider in new[] { "claude", "codex" })
            {
                _ = ReadAdapter(provider, entry.CapabilityId);
            }
        }
    }

    private static void RequireString(
        string value,
        string propertyName,
        string expected)
    {
        if (!string.Equals(
                RequiredString(value, propertyName),
                expected,
                StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                string.Concat(
                    "Consumer capability catalog property '",
                    propertyName,
                    "' is unsupported."));
        }
    }

    private static string RequiredString(
        string value,
        string propertyName,
        bool allowEmpty = false)
    {
        if (value is null || (!allowEmpty && string.IsNullOrWhiteSpace(value)))
        {
            throw new InvalidDataException(
                string.Concat(
                    "Consumer capability catalog property '",
                    propertyName,
                    "' is required."));
        }

        return value;
    }

    private static ImmutableArray<string> ValidateStrings(
        ImmutableArray<string> values,
        string propertyName)
    {
        if (values.IsDefault)
        {
            throw new InvalidDataException(
                string.Concat(
                    "Consumer capability catalog array '",
                    propertyName,
                    "' is required."));
        }

        if (values.Any(string.IsNullOrWhiteSpace) ||
            values.Distinct(StringComparer.Ordinal).Count() != values.Length)
        {
            throw new InvalidDataException(
                string.Concat(
                    "Consumer capability catalog array '",
                    propertyName,
                    "' contains invalid or duplicate values."));
        }

        return values;
    }

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());
}
