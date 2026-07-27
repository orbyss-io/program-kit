namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation.TestSupport;

internal sealed class AuthoringTemporaryDirectory : IDisposable
{
    public AuthoringTemporaryDirectory()
    {
        Path = System.IO.Path.Combine(
            System.IO.Path.GetTempPath(),
            string.Concat("pkcg-authoring-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(Path);
    }

    public string Path { get; }

    public void Dispose()
    {
        if (Directory.Exists(Path))
        {
            Directory.Delete(Path, recursive: true);
        }
    }
}
