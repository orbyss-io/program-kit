using Azure;
using Azure.AI.DocumentIntelligence;
using Azure.Core.Pipeline;

namespace ProgramKit.Examples.Ocr;

/// <summary>Uses the exact public SDK in Started mode, with no model, fallback or implicit polling.</summary>
public static class NativeOcrSubmission
{
    /// <summary>Submits once through an explicitly owned qualified transport.</summary>
    public static async Task SubmitAsync(OcrEnvelope envelope, string credential, OcrSubmissionHandler handler,
        CancellationToken cancellationToken)
    {
        using var http = new HttpClient(handler, disposeHandler: false) { Timeout = Timeout.InfiniteTimeSpan };
        var options = new DocumentIntelligenceClientOptions(DocumentIntelligenceClientOptions.ServiceVersion.V2024_11_30)
        {
            Transport = new HttpClientTransport(http)
        };
        options.Retry.MaxRetries = 0;
        options.Diagnostics.IsLoggingEnabled = false;
        options.Diagnostics.IsLoggingContentEnabled = false;
        options.Diagnostics.IsDistributedTracingEnabled = false;
        var client = new DocumentIntelligenceClient(envelope.Endpoint, new AzureKeyCredential(credential), options);
        var request = new AnalyzeDocumentOptions("prebuilt-read", envelope.Content())
        {
            Pages = "1", OutputContentFormat = DocumentContentFormat.Text
        };
        var operation = await client.AnalyzeDocumentAsync(WaitUntil.Started, request, cancellationToken);
        using var response = operation.GetRawResponse();
        if (response.Status != 202) throw new InvalidDataException("Missing native OCR acknowledgement.");
    }
}
