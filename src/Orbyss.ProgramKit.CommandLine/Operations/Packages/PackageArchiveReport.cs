using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Validated dependency and content report extracted from one exact nupkg.</summary>
public sealed record PackageArchiveReport(
    ImmutableArray<LocalPackageDependency> Dependencies,
    ImmutableArray<LocalPackageContentEntry> Contents);
