using NuGet.Packaging;

if (args.Length != 1 || !File.Exists(args[0]))
    return 2;
using var archive = new PackageArchiveReader(args[0]);
// NuGet's content identity excludes the signature envelope for signed packages.
// Compute it from the actual archive with the selected SDK implementation.
Console.WriteLine(archive.GetContentHash(CancellationToken.None));
return 0;
