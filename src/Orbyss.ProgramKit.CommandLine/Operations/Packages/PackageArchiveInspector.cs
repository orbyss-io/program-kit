using System.Collections.Immutable;
using System.IO.Compression;
using System.Xml;
using System.Xml.Linq;
using Orbyss.ProgramKit.CommandLine.Operations.Local;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Strict nupkg inspector for exact package identity and immutable reports.</summary>
public sealed class PackageArchiveInspector : IPackageArchiveInspector
{
    /// <inheritdoc />
    public PackageArchiveReport Inspect(
        ReadOnlyMemory<byte> packageBytes,
        string expectedPackageId,
        string expectedVersion)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(expectedPackageId);
        ArgumentException.ThrowIfNullOrWhiteSpace(expectedVersion);
        using var stream = new MemoryStream(packageBytes.ToArray(), writable: false);
        using var archive = new ZipArchive(
            stream,
            ZipArchiveMode.Read,
            leaveOpen: false);
        var nuspecs = archive.Entries.Where(static entry =>
                entry.FullName.EndsWith(".nuspec", StringComparison.OrdinalIgnoreCase))
            .ToArray();
        if (nuspecs.Length != 1)
        {
            throw new InvalidDataException(
                "A prepared package must contain exactly one nuspec.");
        }

        var document = ReadNuspec(nuspecs[0]);
        var metadata = document.Root?.Elements().SingleOrDefault(static element =>
            string.Equals(
                element.Name.LocalName,
                "metadata",
                StringComparison.Ordinal));
        var packageId = RequiredElement(metadata, "id");
        var packageVersion = RequiredElement(metadata, "version");
        if (!string.Equals(packageId, expectedPackageId, StringComparison.Ordinal) ||
            !string.Equals(packageVersion, expectedVersion, StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                "The prepared nupkg identity/version does not match its explicit workspace selection.");
        }

        return new PackageArchiveReport(
            ReadDependencies(metadata),
            ReadContents(archive));
    }

    private static XDocument ReadNuspec(ZipArchiveEntry entry)
    {
        using var stream = entry.Open();
        using var reader = XmlReader.Create(
            stream,
            new XmlReaderSettings
            {
                DtdProcessing = DtdProcessing.Prohibit,
                XmlResolver = null,
            });
        return XDocument.Load(reader, LoadOptions.None);
    }

    private static string RequiredElement(XElement? parent, string name)
    {
        var matches = parent?.Elements().Where(element =>
                string.Equals(
                    element.Name.LocalName,
                    name,
                    StringComparison.Ordinal))
            .ToArray() ?? [];
        if (matches.Length != 1 || string.IsNullOrWhiteSpace(matches[0].Value))
        {
            throw new InvalidDataException(
                string.Concat("The package nuspec requires one ", name, "."));
        }

        return matches[0].Value;
    }

    private static ImmutableArray<LocalPackageDependency> ReadDependencies(
        XElement? metadata)
    {
        var dependencies = metadata?.Elements().SingleOrDefault(static element =>
            string.Equals(
                element.Name.LocalName,
                "dependencies",
                StringComparison.Ordinal));
        if (dependencies is null)
        {
            return [];
        }

        var reports = ImmutableArray.CreateBuilder<LocalPackageDependency>();
        foreach (var child in dependencies.Elements())
        {
            if (string.Equals(
                    child.Name.LocalName,
                    "group",
                    StringComparison.Ordinal))
            {
                var target = child.Attribute("targetFramework")?.Value ?? "any";
                AddDependencies(reports, child.Elements(), target);
            }
            else if (string.Equals(
                         child.Name.LocalName,
                         "dependency",
                         StringComparison.Ordinal))
            {
                AddDependency(reports, child, "any");
            }
        }

        return reports
            .OrderBy(static dependency => dependency.TargetFramework, StringComparer.Ordinal)
            .ThenBy(static dependency => dependency.PackageId, StringComparer.Ordinal)
            .ThenBy(static dependency => dependency.VersionRange, StringComparer.Ordinal)
            .ToImmutableArray();
    }

    private static void AddDependencies(
        ImmutableArray<LocalPackageDependency>.Builder reports,
        IEnumerable<XElement> elements,
        string target)
    {
        foreach (var element in elements.Where(static candidate =>
                     string.Equals(
                         candidate.Name.LocalName,
                         "dependency",
                         StringComparison.Ordinal)))
        {
            AddDependency(reports, element, target);
        }
    }

    private static void AddDependency(
        ImmutableArray<LocalPackageDependency>.Builder reports,
        XElement element,
        string target)
    {
        var id = element.Attribute("id")?.Value;
        var version = element.Attribute("version")?.Value;
        if (string.IsNullOrWhiteSpace(id) || string.IsNullOrWhiteSpace(version))
        {
            throw new InvalidDataException(
                "Every package dependency requires an ID and version range.");
        }

        reports.Add(new LocalPackageDependency(target, id, version));
    }

    private static ImmutableArray<LocalPackageContentEntry> ReadContents(
        ZipArchive archive)
    {
        var contents = ImmutableArray.CreateBuilder<LocalPackageContentEntry>();
        foreach (var entry in archive.Entries
                     .Where(static item => item.Name.Length != 0)
                     .OrderBy(static item => item.FullName, StringComparer.Ordinal))
        {
            var relativePath = entry.FullName.Replace('\\', '/');
            LocalOperationPaths.RequireNormalizedRelativePath(
                relativePath,
                "A package archive entry");
            using var stream = entry.Open();
            using var buffer = new MemoryStream();
            stream.CopyTo(buffer);
            var bytes = buffer.ToArray();
            contents.Add(
                new LocalPackageContentEntry(
                    relativePath,
                    bytes.LongLength,
                    LocalOperationHashes.Sha256(bytes)));
        }

        return contents.ToImmutable();
    }
}
