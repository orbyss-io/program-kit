using System.Text.Json;

namespace ProgramKit.Examples.Ocr;

/// <summary>One explicitly scoped public REST observation/deletion; never submits or polls in a loop.</summary>
public static class NativeOcrRecovery
{
    /// <summary>Reports safe status/hash; a deletion acknowledgement never establishes absence.</summary>
    public static async Task<(string Status, byte[]? Result)> ExecuteAsync(WorkerTicket ticket, HttpMessageHandler terminal,
        string credential, CancellationToken cancellationToken)
    {
        if (!Guid.TryParseExact(ticket.ResultHandle,"D",out var id) || ticket.ResultHandle!=id.ToString("D"))
            throw new InvalidDataException("Missing original provider operation handle.");
        var uri = new Uri(new Uri(ticket.Endpoint),"/documentintelligence/documentModels/prebuilt-read/analyzeResults/"+ticket.ResultHandle+"?api-version=2024-11-30");
        using var http = new HttpClient(terminal,disposeHandler:false) { Timeout=Timeout.InfiniteTimeSpan };
        using var request = new HttpRequestMessage(ticket.Action=="poll" ? HttpMethod.Get : HttpMethod.Delete,uri);
        request.Headers.Add("Ocp-Apim-Subscription-Key",credential);
        cancellationToken.ThrowIfCancellationRequested();
        using var response = await http.SendAsync(request,HttpCompletionOption.ResponseHeadersRead,cancellationToken);
        await response.Content.LoadIntoBufferAsync(ticket.MaximumResponseBytes,cancellationToken);
        cancellationToken.ThrowIfCancellationRequested();
        if (ticket.Action=="delete") return ("unknown",null);
        if (response.StatusCode==System.Net.HttpStatusCode.NotFound) return ("absent",null);
        if (!response.IsSuccessStatusCode) return ("unknown",null);
        var body = await response.Content.ReadAsByteArrayAsync(cancellationToken);
        using var json = JsonDocument.Parse(body,new JsonDocumentOptions { MaxDepth=32 });
        var status = json.RootElement.GetProperty("status").GetString();
        if (status is "running" or "notStarted") return ("running",null);
        if (status=="failed") return ("failed",null);
        if (status!="succeeded") return ("unknown",null);
        var result = json.RootElement.GetProperty("analyzeResult");
        var pages = result.GetProperty("pages").EnumerateArray().ToArray();
        if (result.GetProperty("modelId").GetString()!="prebuilt-read" || pages.Length!=1
            || pages[0].GetProperty("pageNumber").GetInt32()!=1)
            throw new InvalidDataException("Provider result exceeds the admitted one-page Read operation.");
        cancellationToken.ThrowIfCancellationRequested();
        return ("succeeded",body);
    }
}
