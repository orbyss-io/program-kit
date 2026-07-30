using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Schemas;

/// <summary>Validated package-owned schema bytes from the explicit module set.</summary>
public sealed class SchemaCatalog : ISchemaCatalog
{
    private static readonly UTF8Encoding Utf8 = new(false);
    private readonly Dictionary<string, SchemaCatalogEntry> byExactId;

    /// <summary>Builds and verifies the finite catalog without runtime discovery.</summary>
    public SchemaCatalog(IEnumerable<IProgramKitSchemaModule> modules)
    {
        ArgumentNullException.ThrowIfNull(modules);
        var moduleArray = modules.ToArray();
        if (moduleArray.Length == 0)
        {
            throw new ArgumentException(
                "At least one schema module is required.",
                nameof(modules));
        }

        var candidates = new List<SchemaCatalogCandidate>();
        foreach (var module in moduleArray)
        {
            ArgumentNullException.ThrowIfNull(module);
            foreach (var resource in module.Resources)
            {
                using var stream = module.OpenRead(resource.SchemaReference);
                using MemoryStream buffer = new();
                stream.CopyTo(buffer);
                var content = buffer.ToArray();
                var digest = string.Concat(
                    "sha256:",
                    Convert.ToHexString(SHA256.HashData(content))
                        .ToLowerInvariant());
                if (!string.Equals(
                        digest,
                        resource.SchemaReference.Digest.Value,
                        StringComparison.Ordinal))
                {
                    throw new InvalidDataException(
                        string.Concat(
                            "Registered schema bytes do not match ",
                            resource.SchemaReference.Identity.Value,
                            "@",
                            resource.SchemaReference.Version.Value,
                            "."));
                }

                candidates.Add(
                    new SchemaCatalogCandidate(
                        resource.SchemaReference.Identity.Value,
                        resource.SchemaReference.Version.Value,
                        resource.CanonicalUri.AbsoluteUri,
                        digest,
                        resource.OwnerId.Value,
                        content,
                        resource));
            }
        }

        var duplicateId = candidates.GroupBy(
                static item => item.ExactId,
                StringComparer.Ordinal)
            .FirstOrDefault(static group => group.Count() != 1);
        var duplicateUri = candidates.GroupBy(
                static item => StripFragment(item.CanonicalUri),
                StringComparer.Ordinal)
            .FirstOrDefault(static group => group.Count() != 1);
        if (duplicateId is not null || duplicateUri is not null)
        {
            throw new InvalidDataException(
                "Schema identities and canonical URIs must resolve exactly once.");
        }

        var exactByUri = candidates.ToDictionary(
            static item => StripFragment(item.CanonicalUri),
            static item => item.ExactId,
            StringComparer.Ordinal);
        Entries = candidates
            .Select(
                candidate => new SchemaCatalogEntry(
                    candidate.Id,
                    candidate.Version,
                    candidate.ExactId,
                    candidate.CanonicalUri,
                    candidate.Sha256,
                    candidate.OwnerId,
                    ReadDependencies(candidate, exactByUri),
                    candidate.Content,
                    candidate.Resource))
            .OrderBy(static item => item.ExactId, StringComparer.Ordinal)
            .ToImmutableArray();
        byExactId = Entries.ToDictionary(
            static item => item.ExactId,
            StringComparer.Ordinal);
    }

    /// <inheritdoc />
    public ImmutableArray<SchemaCatalogEntry> Entries { get; }

    /// <inheritdoc />
    public SchemaCatalogEntry Resolve(string exactId)
    {
        if (string.IsNullOrWhiteSpace(exactId) ||
            !byExactId.TryGetValue(exactId, out var entry))
        {
            throw new CommandInvocationException(
                string.Concat(
                    "Schema '",
                    exactId,
                    "' is not registered. Use 'program-kit schemas list'."),
                "/arguments/schema-id");
        }

        return entry;
    }

    /// <inheritdoc />
    public byte[] Render(string format) =>
        format switch
        {
            "json" => RenderJson(),
            "text" => RenderText(),
            _ => throw new CommandInvocationException(
                "Schema catalog format must be one of: json, text.",
                "/options/format"),
        };

    private byte[] RenderText()
    {
        StringBuilder output = new();
        output.Append("Registered Program Kit schemas: ")
            .Append(Entries.Length)
            .AppendLine();
        foreach (var entry in Entries)
        {
            output.Append(entry.ExactId)
                .Append("  ")
                .Append(entry.Sha256)
                .Append("  ")
                .AppendLine(entry.CanonicalUri);
            if (!entry.Dependencies.IsDefaultOrEmpty)
            {
                output.Append("  dependencies: ")
                    .AppendLine(string.Join(", ", entry.Dependencies));
            }
        }

        return Utf8.GetBytes(output.ToString());
    }

    private byte[] RenderJson()
    {
        using MemoryStream output = new();
        using (Utf8JsonWriter writer = new(output))
        {
            writer.WriteStartObject();
            writer.WriteStartArray("schemas");
            foreach (var entry in Entries)
            {
                writer.WriteStartObject();
                writer.WriteString("canonicalUri", entry.CanonicalUri);
                writer.WriteStartArray("dependencies");
                foreach (var dependency in entry.Dependencies)
                {
                    writer.WriteStringValue(dependency);
                }

                writer.WriteEndArray();
                writer.WriteString("id", entry.Id);
                writer.WriteString("ownerId", entry.OwnerId);
                writer.WriteString("sha256", entry.Sha256);
                writer.WriteString("version", entry.Version);
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteEndObject();
        }

        return output.ToArray();
    }

    private static ImmutableArray<string> ReadDependencies(
        SchemaCatalogCandidate candidate,
        Dictionary<string, string> exactByUri)
    {
        HashSet<string> dependencies = new(StringComparer.Ordinal);
        Utf8JsonReader reader = new(candidate.Content);
        while (reader.Read())
        {
            if (reader.TokenType != JsonTokenType.PropertyName ||
                !reader.ValueTextEquals("$ref"))
            {
                continue;
            }

            if (!reader.Read())
            {
                throw new InvalidDataException(
                    string.Concat(
                        "Schema property $ref in '",
                        candidate.ExactId,
                        "' has no value."));
            }

            if (reader.TokenType == JsonTokenType.String)
            {
                AddReference(reader.GetString());
            }
        }

        return dependencies.Order(StringComparer.Ordinal).ToImmutableArray();

        void AddReference(string? reference)
        {
            if (string.IsNullOrWhiteSpace(reference) ||
                reference.StartsWith('#'))
            {
                return;
            }

            var resolved = new Uri(
                new Uri(candidate.CanonicalUri, UriKind.Absolute),
                reference);
            var key = StripFragment(resolved.AbsoluteUri);
            if (!exactByUri.TryGetValue(key, out var exactId))
            {
                throw new InvalidDataException(
                    string.Concat(
                        "Schema dependency '",
                        key,
                        "' from '",
                        candidate.ExactId,
                        "' is not registered."));
            }

            if (!string.Equals(exactId, candidate.ExactId, StringComparison.Ordinal))
            {
                dependencies.Add(exactId);
            }
        }
    }

    private static string StripFragment(string value)
    {
        var index = value.IndexOf('#', StringComparison.Ordinal);
        return index < 0 ? value : value[..index];
    }

}
