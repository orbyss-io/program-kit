namespace ProgramKit.Examples.PdfDecoding;

public sealed record DecodeLimits(
    int MaximumEncodedBytes,
    int MaximumDecodedBytesPerStream,
    long MaximumTotalDecodedBytes,
    int MaximumDecodeCalls,
    TimeSpan Timeout);
