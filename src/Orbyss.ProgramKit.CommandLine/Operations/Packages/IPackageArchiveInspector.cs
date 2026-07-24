namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Inspects one exact package archive without package-folder discovery.</summary>
public interface IPackageArchiveInspector
{
    /// <summary>Validates identity/version and reports exact archive dependencies and contents.</summary>
    PackageArchiveReport Inspect(
        ReadOnlyMemory<byte> packageBytes,
        string expectedPackageId,
        string expectedVersion);
}
