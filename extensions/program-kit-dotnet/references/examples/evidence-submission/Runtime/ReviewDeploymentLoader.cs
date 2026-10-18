using System.Text.Json;

namespace ProgramKit.Examples.Evidence;

/// <summary>Caller owns the private stream, cancellation and disposal; loading is explicit and bounded.</summary>
public static class ReviewDeploymentLoader
{
    /// <summary>Explicit bounded loading; the caller retains stream ownership and disposal.</summary>
    public static async Task<ReviewDeployment> LoadAsync(Stream input, CancellationToken cancellation)
    {
        var buffer = new byte[1025];
        var count = 0;
        while (count < buffer.Length)
        {
            var remaining = buffer.AsMemory(count);
            var read = await input.ReadAsync(remaining, cancellation);
            if (read == 0) break;
            count += read;
        }
        if (count > 1024) throw new InvalidDataException("Deployment document exceeds its bound.");
        var memory = buffer.AsMemory(0, count);
        var options = new JsonDocumentOptions { MaxDepth = 4 };
        try
        {
            using var document = JsonDocument.Parse(memory, options);
            var root = document.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
                throw new InvalidDataException("Deployment document must be an object.");
            var fields = root.EnumerateObject();
            if (fields.Count() != 1 || !root.TryGetProperty("desk", out var value))
                throw new InvalidDataException("Deployment document has unsupported fields.");
            var desk = value.GetString() ?? "";
            return new ReviewDeployment(desk);
        }
        catch (JsonException)
        {
            throw new InvalidDataException("Deployment document is invalid.");
        }
    }
}
