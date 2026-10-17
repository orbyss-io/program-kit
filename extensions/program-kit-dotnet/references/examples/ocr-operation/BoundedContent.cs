namespace ProgramKit.Examples.Ocr;

/// <summary>Reads an owned file without allocating beyond the declared envelope.</summary>
public static class BoundedContent
{
    /// <summary>Rejects extra bytes even when a file changes after opening.</summary>
    public static async Task<byte[]> ReadFileAsync(string path, int maximumBytes, CancellationToken cancellationToken)
    {
        if (maximumBytes is < 1 or > 1048576) throw new ArgumentOutOfRangeException(nameof(maximumBytes));
        await using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 8192, useAsync:true);
        using var content = new MemoryStream(Math.Min(maximumBytes,8192));
        var buffer = new byte[8192];
        while (true)
        {
            var count = await stream.ReadAsync(buffer.AsMemory(0,Math.Min(buffer.Length,maximumBytes-(int)content.Length+1)),cancellationToken);
            if (count==0) break;
            if (content.Length+count>maximumBytes) throw new InvalidDataException("Owned input exceeds its declared bound.");
            content.Write(buffer,0,count);
        }
        return content.ToArray();
    }
}
