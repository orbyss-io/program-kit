namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

internal sealed class TemporaryTestDirectory :
    IDisposable
{
    private readonly DirectoryInfo directory;

    internal TemporaryTestDirectory(string prefix)
    {
        directory = Directory.CreateTempSubdirectory(prefix);
    }

    internal string FullName => directory.FullName;

    public void Dispose()
    {
        var temporaryRoot = Path.GetFullPath(Path.GetTempPath());
        var target = Path.GetFullPath(directory.FullName);
        if (!target.StartsWith(
                temporaryRoot,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "Refusing to clean a directory outside the temporary root.");
        }

        directory.Refresh();
        if (directory.Exists)
        {
            directory.Delete(recursive: true);
        }
    }
}
