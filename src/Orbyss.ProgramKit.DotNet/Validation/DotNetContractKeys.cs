namespace Orbyss.ProgramKit.DotNet.Validation;

internal static class DotNetContractKeys
{
    internal static string Exact(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

    internal static string Revision(ArtifactReference reference) =>
        string.Concat(reference.Identity.Value, "@", reference.Version.Value);

    internal static string Package(
        Orbyss.ProgramKit.DotNet.Packages.DotNetPackageReference package) =>
        string.Concat(package.PackageId, "@", package.Version.Value);
}
