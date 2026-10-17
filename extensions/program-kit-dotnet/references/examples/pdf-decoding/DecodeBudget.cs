using System.Diagnostics;

namespace ProgramKit.Examples.PdfDecoding;

public sealed class DecodeBudget
{
    private readonly object gate = new();
    private readonly long started = Stopwatch.GetTimestamp();
    private readonly CancellationToken cancellation;
    private long decoded;
    private int calls;
    private bool failed;

    public DecodeBudget(DecodeLimits limits, CancellationToken cancellation = default)
    {
        ArgumentNullException.ThrowIfNull(limits);
        if (limits.MaximumEncodedBytes <= 0 || limits.MaximumDecodedBytesPerStream <= 0 ||
            limits.MaximumTotalDecodedBytes <= 0 || limits.MaximumDecodeCalls <= 0 || limits.Timeout <= TimeSpan.Zero)
            throw new ArgumentOutOfRangeException(nameof(limits));
        Limits = limits;
        this.cancellation = cancellation;
    }

    public DecodeLimits Limits { get; }
    public int Calls { get { lock (gate) return calls; } }
    public long DecodedBytes { get { lock (gate) return decoded; } }

    public void Checkpoint()
    {
        lock (gate)
        {
            cancellation.ThrowIfCancellationRequested();
            if (failed || Stopwatch.GetElapsedTime(started) >= Limits.Timeout)
                throw new InspectionUnavailableException("Decode operation is incomplete, failed or past its cooperative deadline.");
        }
    }

    public void Begin(int encodedBytes)
    {
        lock (gate)
        {
            Checkpoint();
            if (encodedBytes > Limits.MaximumEncodedBytes || calls >= Limits.MaximumDecodeCalls)
                throw new InspectionUnavailableException("Encoded input or decode-call budget exhausted.");
            calls++;
        }
    }

    public void Charge(long streamBytes, int count)
    {
        lock (gate)
        {
            Checkpoint();
            if (count < 0 || streamBytes > Limits.MaximumDecodedBytesPerStream ||
                count > Limits.MaximumTotalDecodedBytes - decoded)
                throw new InspectionUnavailableException("Per-stream or cumulative decoded-byte budget exhausted.");
            decoded += count;
        }
    }

    public void Fail() { lock (gate) failed = true; }
}
