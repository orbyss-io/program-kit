namespace Orbyss.ProgramKit.DotNet.Schemas;

/// <summary>Explicit immutable module for DotNet shell and integrator-document schemas.</summary>
public sealed class DotNetSchemaModule : IProgramKitSchemaModule
{
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersionRange ExactVersion = new("[1.0.0]");
    private static readonly ProgramKitIdentifier Owner =
        new("pkid:package:program-kit:dotnet");
    private static readonly ArtifactProvenance Provenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:design:program-kit:baseline"),
                    new SemanticVersion("0.3.0"),
                    new Sha256Digest("sha256:dbe65ea112a172761f5725c210add00867b8b9f7a180a8b5ee6f80e42dace1c9")),
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:plan:program-kit:baseline"),
                    new SemanticVersion("0.3.0"),
                    new Sha256Digest("sha256:6d7396d5eb71e0d064231110e2ccfcae2aea838ca851b1420ff310df127cd951")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pk-w040-approved-review-set-0-3-0");
    private static readonly ArtifactCompatibility Compatibility =
        new(
            new ProgramKitIdentifier("pkid:contract:program-kit:schema-compatibility-policy"),
            [
                new CompatibilityClaim(
                    CompatibilityDimension.WireRead,
                    CompatibilityClassification.Unknown,
                    []),
                new CompatibilityClaim(
                    CompatibilityDimension.WireWrite,
                    CompatibilityClassification.Unknown,
                    []),
            ],
            ExactVersion,
            ExactVersion,
            []);
    private static readonly ImmutableArray<ProgramKitSchemaResource> Registered =
    [
        Create(
            "dotnet-artifact-input-manifest",
            "artifact-input-manifest.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/artifact-input-manifest.schema.json",
            "f639632bc7f7770847521ffde74f71b1b787e1b357fdaaadc1e98c598ba27929"),
        Create(
            "dotnet-shell-lock",
            "dotnet-shell-lock.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/dotnet-shell-lock.schema.json",
            "a06c12685454d270bb579ea22f65cfba2d809758c1aa803f2cf6e47433ec4e19"),
        Create(
            "dotnet-shell",
            "dotnet-shell.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/dotnet-shell.schema.json",
            "6d79fb385d2fa623a69fa528b23135c0ffd8ac550023ee3d5b177d3b65b5db04"),
        Create(
            "open-console",
            "open-console.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/open-console.schema.json",
            "eed3583dd81b564dd7137e056f650468a17ad31076bdfe938a2520719a73c8e5"),
        Create(
            "open-worker",
            "open-worker.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/open-worker.schema.json",
            "e1b466d192b2d299e9e367daa0991acf6468c855058c4063974e2306bf7628b3"),
        Create(
            "openapi-3-2-0-informational",
            "openapi-3.2.0-2025-11-23.schema.json",
            "https://spec.openapis.org/oas/3.2/schema/2025-11-23",
            "7d48f01f37eeae4799041b371ad5f533f9f533fd2b0caa1011a8ba27c5b48b70"),
    ];

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:dotnet-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => SchemaVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => Registered;

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        var key = ExactKey(schemaReference);
        var resource = Registered.FirstOrDefault(candidate =>
            string.Equals(ExactKey(candidate.SchemaReference), key, StringComparison.Ordinal));
        if (resource is null)
        {
            throw new KeyNotFoundException(
                string.Concat("The exact DotNet schema is not registered: ", key));
        }

        var assembly = typeof(DotNetSchemaModule).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(name =>
            name.EndsWith(resource.ResourceName, StringComparison.Ordinal));
        return assembly.GetManifestResourceStream(resourceName) ??
               throw new InvalidOperationException(
                   string.Concat("The registered DotNet schema is unavailable: ", resource.ResourceName));
    }

    private static ProgramKitSchemaResource Create(
        string name,
        string resourceName,
        string canonicalUri,
        string digest) =>
        new(
            new ArtifactReference(
                new ProgramKitIdentifier(string.Concat("pkid:schema:program-kit:", name)),
                SchemaVersion,
                new Sha256Digest(string.Concat("sha256:", digest))),
            new Uri(canonicalUri, UriKind.Absolute),
            resourceName,
            "application/schema+json",
            Owner,
            ArtifactStatus.Implemented,
            [
                new ProgramKitIdentifier("pkid:project:program-kit:workbench"),
                new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
                new ProgramKitIdentifier("pkid:test:program-kit:conformance-tests"),
            ],
            Provenance,
            Compatibility);

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
