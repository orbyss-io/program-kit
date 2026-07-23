using System.Buffers;

namespace Orbyss.ProgramKit.Serialization.Json.Serialization;

internal sealed class BoundedJsonBufferWriter : IBufferWriter<byte>
{
    private const int MaximumHeadroom = 16 * 1024;
    private byte[] buffer = [];
    private int writtenCount;
    private readonly long maximumBytes;

    internal BoundedJsonBufferWriter(long maximumBytes)
    {
        this.maximumBytes = maximumBytes;
    }

    internal ReadOnlySpan<byte> WrittenSpan =>
        buffer.AsSpan(0, writtenCount);

    public void Advance(int count)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(count);
        ArgumentOutOfRangeException.ThrowIfGreaterThan(
            count,
            buffer.Length - writtenCount);

        if (writtenCount > maximumBytes - count)
        {
            throw new JsonByteLimitExceededException();
        }

        writtenCount += count;
    }

    public Memory<byte> GetMemory(int sizeHint = 0) =>
        GetWritableMemory(sizeHint);

    public Span<byte> GetSpan(int sizeHint = 0) =>
        GetWritableMemory(sizeHint).Span;

    private Memory<byte> GetWritableMemory(int sizeHint)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(sizeHint);

        var requiredHint = Math.Max(sizeHint, 1);
        var capacityCeiling = Math.Min(
            int.MaxValue,
            maximumBytes > int.MaxValue - MaximumHeadroom
                ? int.MaxValue
                : maximumBytes + MaximumHeadroom);
        var requiredCapacity = (long)writtenCount + requiredHint;
        if (requiredCapacity > capacityCeiling)
        {
            throw new JsonByteLimitExceededException();
        }

        if (requiredCapacity > buffer.Length)
        {
            var doubledCapacity = Math.Max(256L, (long)buffer.Length * 2);
            var newCapacity = (int)Math.Min(
                capacityCeiling,
                Math.Max(requiredCapacity, doubledCapacity));
            Array.Resize(ref buffer, newCapacity);
        }

        return buffer.AsMemory(writtenCount);
    }
}
