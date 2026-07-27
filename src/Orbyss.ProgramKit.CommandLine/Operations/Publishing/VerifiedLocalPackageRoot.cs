using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Canonical package-root manifest whose declared nupkg bytes were reverified.</summary>
public sealed record VerifiedLocalPackageRoot(
    string RootPath,
    LocalPackageRootManifest Manifest,
    Sha256Digest ManifestDigest);
