using System.Collections.Immutable;
using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;

namespace Orbyss.ProgramKit.ConformanceTests.Schemas;

[TestClass]
public sealed class ActiveOwnedAlphaTransitionConformanceTests
{
    private const string SelectionRelativePath =
        "extensions/alpha-version-transition/active-owned-schema-migration-selection.json";
    private const string MapRelativePath =
        "extensions/alpha-version-transition/active-owned-alpha-transition-map.json";
    private const string InventoryRelativePath =
        "extensions/alpha-version-transition/version-intent-inventory.json";
    private const string BoundaryRelativePath =
        "extensions/alpha-version-transition/version-intent-observation-boundary.json";

    [TestMethod]
    public void EverySelectedLegacySchemaHasOneExactAlphaTargetAndMigration()
    {
        var root = ConformanceInputs.RepositoryRoot;
        using var selection = ReadRepositoryJson(root, SelectionRelativePath);
        var entries = selection.RootElement.GetProperty("entries")
            .EnumerateArray()
            .ToArray();
        Assert.HasCount(71, entries);
        Assert.HasCount(
            entries.Length,
            entries.Select(GetIdentity).Distinct(StringComparer.Ordinal));
        Assert.HasCount(
            entries.Length,
            entries.Select(GetSourcePath).Distinct(StringComparer.Ordinal));
        Assert.HasCount(
            entries.Length,
            entries.Select(GetTargetPath).Distinct(StringComparer.Ordinal));

        foreach (var entry in entries)
        {
            var identity = GetIdentity(entry);
            var sourceVersion = GetRequiredString(entry, "sourceVersion");
            var targetVersion = GetRequiredString(entry, "targetVersion");
            var ordinal = entry.GetProperty("ownedRevisionOrdinal").GetInt32();
            Assert.AreEqual(
                string.Concat(
                    "0.1.0-alpha.",
                    ordinal.ToString(CultureInfo.InvariantCulture)),
                targetVersion,
                identity);

            var sourcePath = RepositoryPath(root, GetSourcePath(entry));
            var targetPath = RepositoryPath(root, GetTargetPath(entry));
            Assert.AreEqual(
                GetRequiredString(entry, "sourceDigest"),
                Digest(sourcePath),
                sourcePath);
            Assert.IsTrue(File.Exists(targetPath), targetPath);

            using var target = JsonDocument.Parse(File.ReadAllBytes(targetPath));
            Assert.AreEqual(
                identity,
                GetRequiredString(target.RootElement, "x-program-kit-identity"));
            Assert.AreEqual(
                targetVersion,
                GetRequiredString(target.RootElement, "x-program-kit-version"));
            Assert.AreEqual(
                GetRequiredString(entry, "targetCanonicalId"),
                GetRequiredString(target.RootElement, "$id"));

            var suffix = identity["pkid:schema:program-kit:".Length..];
            var migrationPath = RepositoryPath(
                root,
                string.Concat(
                    "extensions/alpha-version-transition/migrations/active-owned-schemas/",
                    suffix,
                    "-to-alpha-",
                    ordinal.ToString(CultureInfo.InvariantCulture),
                    ".migration.json"));
            using var migration = JsonDocument.Parse(
                File.ReadAllBytes(migrationPath));
            Assert.AreEqual(
                identity,
                GetRequiredString(migration.RootElement, "sourceIdentity"));
            Assert.AreEqual(
                string.Concat("[", sourceVersion, "]"),
                GetRequiredString(migration.RootElement, "sourceRange"));
            var targetReference = migration.RootElement.GetProperty("target");
            Assert.AreEqual(
                targetVersion,
                GetRequiredString(targetReference, "version"));
            Assert.AreEqual(
                Digest(targetPath),
                GetRequiredString(targetReference, "digest"));
        }
    }

    [TestMethod]
    public void TransitionMapClosesEverySelectedMigrationExactlyOnce()
    {
        var root = ConformanceInputs.RepositoryRoot;
        using var selection = ReadRepositoryJson(root, SelectionRelativePath);
        using var map = ReadRepositoryJson(root, MapRelativePath);
        var entries = selection.RootElement.GetProperty("entries")
            .EnumerateArray()
            .ToArray();
        var nodes = map.RootElement.GetProperty("nodes")
            .EnumerateArray()
            .ToArray();
        var edges = map.RootElement.GetProperty("edges")
            .EnumerateArray()
            .ToArray();

        Assert.HasCount((entries.Length * 2) + 2, nodes);
        Assert.HasCount(entries.Length + 1, edges);
        Assert.HasCount(
            nodes.Length,
            nodes.Select(NodeExactKey).Distinct(StringComparer.Ordinal));
        Assert.HasCount(
            edges.Length,
            edges.Select(edge => GetRequiredString(edge, "id"))
                .Distinct(StringComparer.Ordinal));

        foreach (var entry in entries)
        {
            var identity = GetIdentity(entry);
            var targetVersion = GetRequiredString(entry, "targetVersion");
            var targetDigest = Digest(
                RepositoryPath(root, GetTargetPath(entry)));
            Assert.HasCount(
                1,
                edges.Where(edge =>
                    GetRequiredString(
                        edge.GetProperty("source"),
                        "identity") == identity &&
                    GetRequiredString(
                        edge.GetProperty("source"),
                        "version") == targetVersion &&
                    GetRequiredString(
                        edge.GetProperty("source"),
                        "digest") == targetDigest));
        }
    }

    [TestMethod]
    public void EveryProgramKitSchemaIdentityIsAlphaOrHasAReviewedAlphaSelection()
    {
        var root = ConformanceInputs.RepositoryRoot;
        using var selection = ReadRepositoryJson(root, SelectionRelativePath);
        var selected = selection.RootElement.GetProperty("entries")
            .EnumerateArray()
            .Select(GetIdentity)
            .ToHashSet(StringComparer.Ordinal);
        var schemas = Directory.EnumerateFiles(
                RepositoryPath(root, "schemas"),
                "*.schema.json",
                SearchOption.AllDirectories)
            .Where(path => !Normalize(path).Contains(
                "/vendor/",
                StringComparison.Ordinal))
            .Select(ReadSchemaIdentityAndVersion)
            .Where(static candidate =>
                candidate.Identity is not null &&
                candidate.Identity.StartsWith(
                    "pkid:schema:program-kit:",
                    StringComparison.Ordinal))
            .ToArray();

        foreach (var group in schemas.GroupBy(
                     static candidate => candidate.Identity!,
                     StringComparer.Ordinal))
        {
            Assert.IsTrue(
                group.Any(static candidate =>
                    candidate.Version!.StartsWith(
                        "0.1.0-alpha.",
                        StringComparison.Ordinal)) ||
                selected.Contains(group.Key),
                group.Key);
        }
    }

    [TestMethod]
    public void VersionIntentInventoryClosesActiveAndProtectedSourceClasses()
    {
        var root = ConformanceInputs.RepositoryRoot;
        using var inventory = ReadRepositoryJson(root, InventoryRelativePath);
        using var boundary = ReadRepositoryJson(root, BoundaryRelativePath);
        var entries = inventory.RootElement.GetProperty("entries")
            .EnumerateArray()
            .ToArray();
        Assert.HasCount(130, entries);
        Assert.HasCount(
            entries.Length,
            entries.Select(entry => string.Concat(
                    GetRequiredString(entry, "sourcePath"),
                    "\n",
                    GetRequiredString(entry, "sourceLocator")))
                .Distinct(StringComparer.Ordinal));

        foreach (var entry in entries)
        {
            var path = RepositoryPath(
                root,
                GetRequiredString(entry, "sourcePath"));
            Assert.AreEqual(
                GetRequiredString(entry, "sourceDigest"),
                Digest(path),
                path);
            var currentValue = GetRequiredString(entry, "currentValue");
            if (!string.Equals(
                    currentValue,
                    "exact-central-package-selections",
                    StringComparison.Ordinal))
            {
                Assert.Contains(currentValue, File.ReadAllText(path), path);
            }
        }

        var protectedClassifications = boundary.RootElement
            .GetProperty("protectedSourceClasses")
            .EnumerateArray()
            .Select(entry => GetRequiredString(entry, "classification"))
            .ToHashSet(StringComparer.Ordinal);
        Assert.IsTrue(protectedClassifications.SetEquals(
            [
                "external-selection",
                "fixture-revision",
                "historical-evidence-revision",
            ]));

        var evidence = inventory.RootElement
            .GetProperty("completenessEvidence")[0];
        Assert.AreEqual(
            Digest(RepositoryPath(root, BoundaryRelativePath)),
            GetRequiredString(evidence, "digest"));

        var model = new VersionIntentInventoryDocument(
            GetRequiredString(inventory.RootElement, "repositoryRoot"),
            inventory.RootElement.GetProperty("sourceRoots")
                .EnumerateArray()
                .Select(static rootElement => rootElement.GetString()!)
                .ToImmutableArray(),
            entries.Select(ToInventoryEntry).ToImmutableArray(),
            [
                new ArtifactReference(
                    ProgramKitIdentifier.Parse(
                        GetRequiredString(evidence, "identity")),
                    SemanticVersion.Parse(
                        GetRequiredString(evidence, "version")),
                    Sha256Digest.Parse(
                        GetRequiredString(evidence, "digest"))),
            ]);
        VersionIntentInventoryDocumentValidator validator = new();
        var validation = validator.Validate(model);
        Assert.IsTrue(
            validation.IsValid,
            string.Join(
                Environment.NewLine,
                validation.Diagnostics.Select(static diagnostic =>
                    string.Concat(
                        diagnostic.Id,
                        " ",
                        diagnostic.Path,
                        " ",
                        diagnostic.Message))));
    }

    private static JsonDocument ReadRepositoryJson(
        string root,
        string relativePath) =>
        JsonDocument.Parse(File.ReadAllBytes(RepositoryPath(root, relativePath)));

    private static string RepositoryPath(string root, string relativePath) =>
        Path.Combine(root, relativePath.Replace('/', Path.DirectorySeparatorChar));

    private static string GetIdentity(JsonElement entry) =>
        GetRequiredString(entry, "identity");

    private static string GetSourcePath(JsonElement entry) =>
        GetRequiredString(entry, "sourcePath");

    private static string GetTargetPath(JsonElement entry) =>
        GetRequiredString(entry, "targetPath");

    private static string GetRequiredString(
        JsonElement element,
        string propertyName) =>
        element.GetProperty(propertyName).GetString() ??
        throw new AssertFailedException(
            string.Concat("Missing string property: ", propertyName));

    private static string NodeExactKey(JsonElement node)
    {
        var revision = node.GetProperty("revision");
        return string.Concat(
            GetRequiredString(revision, "identity"),
            "@",
            GetRequiredString(revision, "version"),
            "#",
            GetRequiredString(revision, "digest"));
    }

    private static VersionIntentInventoryEntry ToInventoryEntry(
        JsonElement entry)
    {
        var ordinalElement = entry.GetProperty("ownedRevisionOrdinal");
        return new VersionIntentInventoryEntry(
            ProgramKitIdentifier.Parse(GetRequiredString(entry, "identity")),
            ProgramKitIdentifier.Parse(GetRequiredString(entry, "ownerId")),
            GetRequiredString(entry, "sourcePath"),
            GetRequiredString(entry, "sourceLocator"),
            GetRequiredString(entry, "currentValue"),
            Sha256Digest.Parse(GetRequiredString(entry, "sourceDigest")),
            ParseIntent(GetRequiredString(entry, "intent")),
            entry.GetProperty("isActive").GetBoolean(),
            ordinalElement.ValueKind == JsonValueKind.Null
                ? null
                : ordinalElement.GetInt32(),
            ParseDisposition(
                GetRequiredString(entry, "transitionDisposition")));
    }

    private static VersionIntent ParseIntent(string value) =>
        value switch
        {
            "product-release" => VersionIntent.ProductRelease,
            "owned-artifact-revision" => VersionIntent.OwnedArtifactRevision,
            "external-selection" => VersionIntent.ExternalSelection,
            "historical-evidence-revision" =>
                VersionIntent.HistoricalEvidenceRevision,
            "fixture-revision" => VersionIntent.FixtureRevision,
            _ => throw new AssertFailedException(
                string.Concat("Unknown version intent: ", value)),
        };

    private static VersionTransitionDisposition ParseDisposition(
        string value) =>
        value switch
        {
            "coordinate-product-release" =>
                VersionTransitionDisposition.CoordinateProductRelease,
            "migrate-owned-revision" =>
                VersionTransitionDisposition.MigrateOwnedRevision,
            "retain-owned-revision" =>
                VersionTransitionDisposition.RetainOwnedRevision,
            "preserve-external-selection" =>
                VersionTransitionDisposition.PreserveExternalSelection,
            "preserve-historical-evidence" =>
                VersionTransitionDisposition.PreserveHistoricalEvidence,
            "preserve-fixture" =>
                VersionTransitionDisposition.PreserveFixture,
            _ => throw new AssertFailedException(
                string.Concat("Unknown transition disposition: ", value)),
        };

    private static string Digest(string path) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(
                    SHA256.HashData(File.ReadAllBytes(path)))
                .ToLowerInvariant());

    private static (string? Identity, string? Version)
        ReadSchemaIdentityAndVersion(string path)
    {
        using var document = JsonDocument.Parse(File.ReadAllBytes(path));
        return (
            ReadOptionalString(
                document.RootElement,
                "x-program-kit-identity"),
            ReadOptionalString(
                document.RootElement,
                "x-program-kit-version"));
    }

    private static string? ReadOptionalString(
        JsonElement element,
        string propertyName) =>
        element.TryGetProperty(propertyName, out var property)
            ? property.GetString()
            : null;

    private static string Normalize(string path) =>
        path.Replace('\\', '/');
}
