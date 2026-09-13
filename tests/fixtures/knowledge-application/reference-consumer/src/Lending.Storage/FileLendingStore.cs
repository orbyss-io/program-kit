using System.Text.Json;
using Lending.Core;
namespace Lending.Storage;

public sealed class FileLendingStore(string directory) : ILendingStore
{
    private readonly object sync = new();
    public T InTransaction<T>(Func<LendingState, T> operation)
    {
        lock (sync)
        {
            Directory.CreateDirectory(directory);
            var path = Path.Combine(directory, "lending.json");
            var state = File.Exists(path) ? JsonSerializer.Deserialize<LendingState>(File.ReadAllBytes(path))! : new();
            var result = operation(state);
            var temporary = path + ".tmp";
            File.WriteAllBytes(temporary, JsonSerializer.SerializeToUtf8Bytes(state));
            File.Move(temporary, path, true);
            return result;
        }
    }
}
