using System.Net;
using System.Security.Cryptography;
using System.Text.Json;

namespace ProgramKit.Examples.Ocr;

/// <summary>Admits the actual native request once, directly to its owned terminal handler.</summary>
public sealed class OcrSubmissionHandler(OcrEnvelope envelope, Action<string> retainHandle) : DelegatingHandler
{
    private int submissions;
    /// <summary>Gets attempted native dispatch admissions, including rejected retries.</summary>
    public int ObservedSubmissions => Volatile.Read(ref submissions);

    /// <inheritdoc />
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (request.Method != HttpMethod.Post || request.RequestUri?.OriginalString != envelope.SubmissionUri.OriginalString
            || request.Content is null) throw new InvalidDataException("Native request exceeds the exact OCR-only scope.");
        await request.Content.LoadIntoBufferAsync(envelope.MaximumEncodedBytes, cancellationToken);
        var encoded = await request.Content.ReadAsByteArrayAsync(cancellationToken);
        using (var json = JsonDocument.Parse(encoded, new JsonDocumentOptions { MaxDepth = 2 }))
        {
            var fields = json.RootElement.EnumerateObject().ToArray();
            if (fields.Length != 1 || fields[0].Name != "base64Source"
                || Convert.ToHexStringLower(SHA256.HashData(fields[0].Value.GetBytesFromBase64())) != envelope.DocumentSha256)
                throw new InvalidDataException("Native OCR serialized a different input.");
        }
        cancellationToken.ThrowIfCancellationRequested();
        if (Interlocked.Increment(ref submissions) != 1) throw new InvalidOperationException("An OCR authority cannot retry a POST.");
        // DelegatingHandler forwards the already-owned request once. A second
        // HttpClient must never re-send that request or introduce its own retry.
        var response = await base.SendAsync(request, cancellationToken);
        try
        {
            if (response.StatusCode == HttpStatusCode.Accepted)
            {
                if (!response.Headers.TryGetValues("Operation-Location", out var values) || values.Count() != 1
                    || !Uri.TryCreate(values.Single(), UriKind.Absolute, out var location)
                    || location.Scheme != envelope.Endpoint.Scheme || location.Authority != envelope.Endpoint.Authority
                    || location.UserInfo.Length != 0 || location.Fragment.Length != 0 || location.Query != "?api-version=2024-11-30")
                    throw new InvalidDataException("OCR acknowledgement does not identify an owned operation.");
                var text = location.Segments.Last();
                if (!Guid.TryParseExact(text, "D", out var id) || text != id.ToString("D")
                    || location.AbsolutePath != "/documentintelligence/documentModels/prebuilt-read/analyzeResults/" + text)
                    throw new InvalidDataException("OCR acknowledgement has an invalid result identity.");
                retainHandle(text); // Preserve this before any response body work.
            }
            await response.Content.LoadIntoBufferAsync(envelope.MaximumResponseBytes, cancellationToken);
            return response;
        }
        catch { response.Dispose(); throw; }
    }
}
