using System.Text;
using System.Xml;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Exact first-party-local and reviewed-external-NuGet.org source mapping.</summary>
public sealed class NuGetSourceConfigurationWriter :
    INuGetSourceConfigurationWriter
{
    private const string NuGetOrg = "https://api.nuget.org/v3/index.json";

    /// <inheritdoc />
    public ReadOnlyMemory<byte> Write(
        string localPackageRoot,
        LocalPackageRootManifest manifest)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(localPackageRoot);
        ArgumentNullException.ThrowIfNull(manifest);
        var localIds = manifest.Packages
            .Select(static package => package.PackageId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var externalIds = manifest.ExternalPackages
            .Select(static package => package.PackageId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (localIds.Length == 0 ||
            localIds.Distinct(StringComparer.Ordinal).Count() != localIds.Length ||
            externalIds.Distinct(StringComparer.Ordinal).Count() !=
            externalIds.Length ||
            localIds.Intersect(externalIds, StringComparer.Ordinal).Any())
        {
            throw new InvalidDataException(
                "Package source mapping requires disjoint unique first-party and external package IDs.");
        }

        var packageDirectories = manifest.Packages
            .Select(package =>
            {
                var relativeDirectory = Path.GetDirectoryName(
                    package.PackagePath.Replace('/', Path.DirectorySeparatorChar));
                return Path.GetFullPath(
                    relativeDirectory ?? string.Empty,
                    localPackageRoot);
            })
            .Distinct(
                OperatingSystem.IsWindows()
                    ? StringComparer.OrdinalIgnoreCase
                    : StringComparer.Ordinal)
            .ToArray();
        if (packageDirectories.Length != 1)
        {
            throw new InvalidDataException(
                "All selected nupkgs must share one manifest-bound local source folder.");
        }

        var builder = new StringBuilder();
        using (var writer = XmlWriter.Create(
                   builder,
                   new XmlWriterSettings
                   {
                       Encoding = new UTF8Encoding(encoderShouldEmitUTF8Identifier: false),
                       Indent = true,
                       NewLineChars = "\n",
                       OmitXmlDeclaration = true,
                   }))
        {
            writer.WriteStartElement("configuration");
            WriteSources(writer, packageDirectories[0]);
            WriteAuditSources(writer);
            writer.WriteStartElement("disabledPackageSources");
            writer.WriteStartElement("clear");
            writer.WriteEndElement();
            writer.WriteEndElement();
            writer.WriteStartElement("fallbackPackageFolders");
            writer.WriteStartElement("clear");
            writer.WriteEndElement();
            writer.WriteEndElement();
            writer.WriteStartElement("packageSourceMapping");
            writer.WriteStartElement("clear");
            writer.WriteEndElement();
            WriteMappings(writer, "first-party", localIds);
            WriteMappings(writer, "nuget.org", externalIds);
            writer.WriteEndElement();
            writer.WriteEndElement();
        }

        return Encoding.UTF8.GetBytes(builder.ToString());
    }

    private static void WriteSources(XmlWriter writer, string localPackageRoot)
    {
        writer.WriteStartElement("packageSources");
        writer.WriteStartElement("clear");
        writer.WriteEndElement();
        WriteAdd(writer, "first-party", localPackageRoot);
        WriteAdd(writer, "nuget.org", NuGetOrg);
        writer.WriteEndElement();
    }

    private static void WriteAuditSources(XmlWriter writer)
    {
        writer.WriteStartElement("auditSources");
        writer.WriteStartElement("clear");
        writer.WriteEndElement();
        WriteAdd(writer, "nuget.org", NuGetOrg);
        writer.WriteEndElement();
    }

    private static void WriteAdd(
        XmlWriter writer,
        string key,
        string value)
    {
        writer.WriteStartElement("add");
        writer.WriteAttributeString("key", key);
        writer.WriteAttributeString("value", value);
        writer.WriteEndElement();
    }

    private static void WriteMappings(
        XmlWriter writer,
        string source,
        IReadOnlyList<string> packageIds)
    {
        writer.WriteStartElement("packageSource");
        writer.WriteAttributeString("key", source);
        foreach (var packageId in packageIds)
        {
            writer.WriteStartElement("package");
            writer.WriteAttributeString("pattern", packageId);
            writer.WriteEndElement();
        }

        writer.WriteEndElement();
    }
}
