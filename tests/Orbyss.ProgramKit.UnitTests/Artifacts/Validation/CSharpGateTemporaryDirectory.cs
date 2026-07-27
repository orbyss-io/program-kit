namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation;

internal sealed class CSharpGateTemporaryDirectory : IDisposable
{
    private readonly DirectoryInfo directory;

    internal CSharpGateTemporaryDirectory(string prefix)
    {
        directory = Directory.CreateTempSubdirectory(prefix);
    }

    internal string FullName => directory.FullName;

    public void Dispose()
    {
        directory.Refresh();
        if (directory.Exists)
        {
            directory.Delete(recursive: true);
        }
    }
}
