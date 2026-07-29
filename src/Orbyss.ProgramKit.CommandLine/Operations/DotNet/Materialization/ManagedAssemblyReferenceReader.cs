using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Reads one immutable managed assembly identity and exact bytes.</summary>
public static class ManagedAssemblyReferenceReader
{
    /// <summary>Reads and hashes one explicit managed reference.</summary>
    public static ManagedAssemblyReference Read(string path, bool consumer)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        var fullPath = Path.GetFullPath(path);
        byte[] content;
        try
        {
            content = File.ReadAllBytes(fullPath);
            using PEReader reader = new(
                new MemoryStream(content, writable: false));
            if (!reader.HasMetadata)
            {
                throw Failure(
                    "An evaluated compilation reference is not managed.",
                    fullPath);
            }

            var metadata = reader.GetMetadataReader();
            var definition = metadata.GetAssemblyDefinition();
            var name = metadata.GetString(definition.Name);
            var culture = definition.Culture.IsNil
                ? "neutral"
                : metadata.GetString(definition.Culture);
            var publicKey = definition.PublicKey.IsNil
                ? []
                : metadata.GetBlobBytes(definition.PublicKey);
            var publicKeyIdentity = publicKey.Length == 0
                ? "null"
                : Convert.ToHexStringLower(publicKey);
            var identity = string.Concat(
                name,
                ", Version=",
                definition.Version,
                ", Culture=",
                culture,
                ", PublicKey=",
                publicKeyIdentity);
            return new ManagedAssemblyReference(
                fullPath,
                name,
                identity,
                definition.Version,
                new Sha256Digest(
                    string.Concat(
                        "sha256:",
                        Convert.ToHexStringLower(SHA256.HashData(content)))),
                content,
                consumer);
        }
        catch (ConsoleInputMaterializationException)
        {
            throw;
        }
        catch (Exception exception) when (
            exception is BadImageFormatException or
                IOException or
                UnauthorizedAccessException)
        {
            throw Failure(
                "An evaluated compilation reference is missing or unreadable.",
                fullPath);
        }
    }

    private static ConsoleInputMaterializationException Failure(
        string message,
        string path) =>
        new(
            ConsoleInputMaterializationDiagnosticIds.InvalidReferenceClosure,
            message,
            path);
}
