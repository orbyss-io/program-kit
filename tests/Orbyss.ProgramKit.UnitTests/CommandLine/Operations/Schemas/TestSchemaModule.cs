using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Schemas;

internal sealed class TestSchemaModule : IProgramKitSchemaModule
{
    private readonly byte[] content;

    internal TestSchemaModule(string name, string canonicalUri, string json)
    {
        content = Encoding.UTF8.GetBytes(json);
        var template = new ArtifactsSchemaModule().Resources[0];
        var reference = new ArtifactReference(
            new ProgramKitIdentifier(string.Concat("pkid:schema:program-kit:", name)),
            new SemanticVersion("0.1.0-alpha.1"),
            new Sha256Digest(string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(content)))));
        Resources =
        [
            template with
            {
                SchemaReference = reference,
                CanonicalUri = new Uri(canonicalUri, UriKind.Absolute),
                ResourceName = string.Concat(name, ".schema.json"),
            },
        ];
        Identity = new ProgramKitIdentifier(
            string.Concat("pkid:catalog:program-kit:test.", name));
    }

    public ProgramKitIdentifier Identity { get; }

    public SemanticVersion Version { get; } = new("0.1.0-alpha.1");

    public ImmutableArray<ProgramKitSchemaResource> Resources { get; }

    public Stream OpenRead(ArtifactReference schemaReference) =>
        schemaReference == Resources[0].SchemaReference
            ? new MemoryStream(content, writable: false)
            : throw new KeyNotFoundException();
}
