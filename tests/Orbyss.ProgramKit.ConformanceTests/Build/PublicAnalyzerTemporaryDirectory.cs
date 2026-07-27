namespace Orbyss.ProgramKit.ConformanceTests.Build;

internal sealed class PublicAnalyzerTemporaryDirectory :
    IDisposable
{
    private readonly string root =
        Directory.CreateTempSubdirectory("program-kit-public-analyzer-")
            .FullName;

    internal string Create(string name)
    {
        var path = Path.Combine(root, name);
        Directory.CreateDirectory(path);
        return path;
    }

    public void Dispose()
    {
        var temporaryRoot = Path.GetFullPath(Path.GetTempPath());
        var target = Path.GetFullPath(root);
        if (!target.StartsWith(
                temporaryRoot,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "Refusing to clean outside the temporary root.");
        }

        if (Directory.Exists(target))
        {
            Directory.Delete(target, recursive: true);
        }
    }
}
