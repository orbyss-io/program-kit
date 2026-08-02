using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Orbyss.ProgramKit.Tests;

internal sealed class SpecKitAdapterTestWorkspace : IDisposable
{
    private readonly string root;

    private SpecKitAdapterTestWorkspace(string root)
    {
        this.root = root;
    }

    public string Root => root;

    public static SpecKitAdapterTestWorkspace Create() => new(TestRepository.CreateEmptyWorkspace());

    public string PathOf(string logicalPath) => Path.Combine(root, logicalPath.Replace('/', Path.DirectorySeparatorChar));

    public void WriteText(string logicalPath, string content)
    {
        string path = PathOf(logicalPath);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, content);
    }

    public IReadOnlyCollection<string> Files() => Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories)
        .Select(path => Path.GetRelativePath(root, path).Replace('\\', '/'))
        .OrderBy(path => path, StringComparer.Ordinal)
        .ToArray();

    public void Dispose() => TestRepository.DeleteWorkspace(root);
}
