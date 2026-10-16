using System.Security.Cryptography;

namespace ProgramKit.Examples.Ocr;

/// <summary>Owns a bounded immutable input for one one-page Read submission.</summary>
public sealed class OcrEnvelope
{
    private readonly byte[] document;
    /// <summary>Gets the single selected provider origin.</summary>
    public Uri Endpoint { get; }
    /// <summary>Gets the exact admitted input digest.</summary>
    public string DocumentSha256 { get; }
    /// <summary>Gets the bounded response envelope.</summary>
    public int MaximumResponseBytes { get; }
    /// <summary>Gets the exact selected SDK request URI.</summary>
    public Uri SubmissionUri => new(Endpoint, "/documentintelligence/documentModels/prebuilt-read:analyze?api-version=2024-11-30&pages=1&stringIndexType=utf16CodeUnit&outputContentFormat=text");

    /// <summary>Copies the original bytes before the SDK can serialize them.</summary>
    public OcrEnvelope(Uri endpoint, byte[] input, string expectedSha256, int maximumInputBytes, int maximumResponseBytes)
    {
        if (endpoint.Scheme != "https" || endpoint.UserInfo.Length != 0 || endpoint.Query.Length != 0
            || endpoint.Fragment.Length != 0 || endpoint.AbsolutePath != "/" || endpoint.Port != 443)
            throw new ArgumentException("Unqualified OCR origin.");
        if (maximumInputBytes is < 1 or > 1048576 || maximumResponseBytes is < 1 or > 1048576 || input.Length > maximumInputBytes)
            throw new ArgumentException("OCR envelope exceeds its admitted bound.");
        document = input.ToArray();
        DocumentSha256 = Convert.ToHexStringLower(SHA256.HashData(document));
        if (DocumentSha256 != expectedSha256) throw new InvalidDataException("Original OCR fixture changed.");
        Endpoint = endpoint;
        MaximumResponseBytes = maximumResponseBytes;
    }

    /// <summary>Supplies an owned copy to native serialization.</summary>
    public BinaryData Content() => BinaryData.FromBytes(document.ToArray());
    /// <summary>Gets the finite encoded request bound.</summary>
    public long MaximumEncodedBytes => ((document.Length + 2L) / 3L) * 4L + 64L;
}
