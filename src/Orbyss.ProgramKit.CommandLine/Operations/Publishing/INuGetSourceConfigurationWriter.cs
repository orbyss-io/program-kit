using Orbyss.ProgramKit.CommandLine.Operations.Packages;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Writes explicit package-source mapping for one verified local package root.</summary>
public interface INuGetSourceConfigurationWriter
{
    /// <summary>Creates deterministic source mapping with no catch-all patterns.</summary>
    ReadOnlyMemory<byte> Write(
        string localPackageRoot,
        LocalPackageRootManifest manifest);
}
