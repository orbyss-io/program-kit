using System.Net;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace ProgramKit.Examples.Ocr;

/// <summary>Consumes one exact engine ticket before any possible provider dispatch.</summary>
public static class NativeWorker
{
    private static void Emit(object value) { Console.WriteLine(JsonSerializer.Serialize(value));Console.Out.Flush(); }

    /// <summary>Runs a single submit/poll/delete. The engine owns authority, accounting and future recovery.</summary>
    public static async Task RunAsync(string ticketPath, string expectedSha256)
    {
        try
        {
            var full = Path.GetFullPath(ticketPath);
            var bytes = await BoundedContent.ReadFileAsync(full,65536,CancellationToken.None);
            using (var parsed = JsonDocument.Parse(bytes,new JsonDocumentOptions { MaxDepth=4 }))
            {
                var names = new HashSet<string>(StringComparer.Ordinal);
                foreach (var property in parsed.RootElement.EnumerateObject())
                    if (!names.Add(property.Name)) throw new InvalidDataException("Duplicate dispatch ticket field.");
            }
            var ticket = JsonSerializer.Deserialize<WorkerTicket>(bytes,new JsonSerializerOptions
            {
                PropertyNamingPolicy=JsonNamingPolicy.CamelCase,PropertyNameCaseInsensitive=false,
                UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow,NumberHandling=JsonNumberHandling.Strict,
                RespectNullableAnnotations=true,RespectRequiredConstructorParameters=true
            }) ?? throw new InvalidDataException("Missing dispatch ticket.");
            var comparison = OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;
            if (ticket.SchemaVersion!=1 || ticket.Kind!="program-kit-ocr-worker-ticket" || ticket.Execution is not ("recording" or "provider")
                || !Guid.TryParseExact(ticket.Attempt,"D",out _) || !Guid.TryParseExact(ticket.Nonce,"D",out _)
                || !string.Equals(full,Path.GetFullPath(ticket.OriginalTicketPath),comparison)
                || Path.GetFileName(full)!=ticket.Nonce+".json" || ticket.Action is not ("submit" or "poll" or "delete")
                || ticket.TimeoutMilliseconds is < 1 or > 60000 || ticket.MaximumResponseBytes is < 1 or > 1048576
                || ticket.MaximumInputBytes is < 1 or > 1048576
                || ticket.Execution=="provider" && ticket.RecordingOutcome is not null)
                throw new InvalidDataException("Unqualified dispatch ticket scope.");
            var endpoint = new Uri(ticket.Endpoint);
            if (!Regex.IsMatch(endpoint.Host,"\\A[a-z0-9][a-z0-9-]{0,62}\\.cognitiveservices\\.azure\\.com\\z")
                || endpoint.Scheme!="https" || endpoint.Port!=443 || endpoint.UserInfo.Length!=0 || endpoint.AbsolutePath!="/"
                || endpoint.Query.Length!=0 || endpoint.Fragment.Length!=0)
                throw new InvalidDataException("Unqualified provider origin.");
            // Refuse aliases before atomic consumption. The exact absolute ticket
            // name is part of its hash; a copied path cannot replay the capability.
            for (FileSystemInfo? entry = new FileInfo(full);entry is not null;entry = entry is FileInfo file ? file.Directory : ((DirectoryInfo)entry).Parent)
                if ((entry.Attributes&FileAttributes.ReparsePoint)!=0) throw new InvalidDataException("Aliased dispatch ticket.");
            File.Move(full,full+".consumed",overwrite:false);
            if (Convert.ToHexStringLower(SHA256.HashData(bytes))!=expectedSha256) throw new InvalidDataException("Dispatch ticket changed.");
            var remaining = Math.Min(ticket.TimeoutMilliseconds,ticket.DeadlineUnixMilliseconds-DateTimeOffset.UtcNow.ToUnixTimeMilliseconds());
            if (remaining<=0) throw new OperationCanceledException("Original dispatch deadline expired.");
            using var deadline = new CancellationTokenSource(TimeSpan.FromMilliseconds(remaining));
            if (ticket.Execution=="recording" && Environment.GetEnvironmentVariable("PROGRAMKIT_OCR_WORKER_KEY") is not null)
                throw new InvalidOperationException("A recording worker must not receive a provider credential.");
            var credential = ticket.Execution=="recording" ? "fictional-key" :
                Environment.GetEnvironmentVariable("PROGRAMKIT_OCR_WORKER_KEY") ?? throw new InvalidOperationException("Missing scoped provider credential.");
            if (ticket.Action=="submit")
            {
                if (ticket.FixturePath is null || ticket.FixtureSha256 is null || ticket.ResultHandle is not null)
                    throw new InvalidDataException("Missing immutable submission fixture.");
                var document = await BoundedContent.ReadFileAsync(ticket.FixturePath,ticket.MaximumInputBytes,deadline.Token);
                var envelope = new OcrEnvelope(endpoint,document,ticket.FixtureSha256,ticket.MaximumInputBytes,ticket.MaximumResponseBytes);
                using var gate = new OcrSubmissionHandler(envelope,id =>
                {
                    Emit(new { @event="handle",handle=id });
                    if (ticket.Execution=="recording" && ticket.RecordingOutcome=="exit-after-handle") Environment.Exit(90);
                }) { InnerHandler=Terminal(ticket,deadline.Token) };
                await NativeOcrSubmission.SubmitAsync(envelope,credential,gate,deadline.Token);
                deadline.Token.ThrowIfCancellationRequested();
                Emit(new { @event="outcome",status="acknowledged",responseSha256=(string?)null });
            }
            else
            {
                using var terminal = Terminal(ticket,deadline.Token);
                var (status,result) = await NativeOcrRecovery.ExecuteAsync(ticket,terminal,credential,deadline.Token);
                if (result is not null)
                {
                    await using var output = new FileStream(full+".result",FileMode.CreateNew,FileAccess.Write,FileShare.None);
                    await output.WriteAsync(result,deadline.Token);output.Flush(flushToDisk:true);
                }
                deadline.Token.ThrowIfCancellationRequested();
                Emit(new { @event="outcome",status,responseSha256=result is null ? null : Convert.ToHexStringLower(SHA256.HashData(result)) });
            }
        }
        catch (Exception error)
        {
            // SDK exception messages/bodies may contain private material. Keep
            // only the type and uncertainty; raw credentials/results are not logs.
            Emit(new { @event="outcome",status="unknown",errorType=error.GetType().Name,responseSha256=(string?)null });
        }
    }

    private static HttpMessageHandler Terminal(WorkerTicket ticket, CancellationToken cancellationToken)
        => ticket.Execution=="recording" ? Recording(ticket,cancellationToken) :
            new SocketsHttpHandler { AllowAutoRedirect=false,UseCookies=false,AutomaticDecompression=DecompressionMethods.None };

    private static RecordingTerminal Recording(WorkerTicket ticket, CancellationToken cancellationToken)
    {
        var allowed = ticket.Action=="submit" ? new[] {"accepted","transport-failure","oversized-response","timeout-after-handle","exit-after-handle","exit-before-transport"} :
            ticket.Action=="poll" ? ["running","succeeded","absent","transport-failure"] : ["delete-accepted","transport-failure"];
        if (!allowed.Contains(ticket.RecordingOutcome,StringComparer.Ordinal)) throw new InvalidDataException("Unknown recording scenario.");
        return new RecordingTerminal((request,token) =>
        {
            if (ticket.RecordingOutcome=="exit-before-transport") Environment.Exit(91);
            Emit(new { @event="recording-transport",method=request.Method.Method });
            if (ticket.RecordingOutcome=="transport-failure") throw new HttpRequestException("Synthetic transport uncertainty.");
            if (ticket.Action=="submit")
            {
                var response = new HttpResponseMessage(HttpStatusCode.Accepted) { Content=new StringContent("{}") };
                response.Headers.TryAddWithoutValidation("Operation-Location",ticket.Endpoint.TrimEnd('/')+"/documentintelligence/documentModels/prebuilt-read/analyzeResults/"+Guid.NewGuid().ToString("D")+"?api-version=2024-11-30");
                if (ticket.RecordingOutcome=="oversized-response") response.Content=new StringContent(new string('x',ticket.MaximumResponseBytes+1));
                if (ticket.RecordingOutcome=="timeout-after-handle") response.Content=new DelayedContent(cancellationToken);
                return Task.FromResult(response);
            }
            if (ticket.Action=="delete") return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NoContent));
            if (ticket.RecordingOutcome=="absent") return Task.FromResult(new HttpResponseMessage(HttpStatusCode.NotFound));
            var payload = ticket.RecordingOutcome=="running" ? "{\"status\":\"running\"}" :
                "{\"status\":\"succeeded\",\"analyzeResult\":{\"modelId\":\"prebuilt-read\",\"pages\":[{\"pageNumber\":1}],\"content\":\"synthetic offline text\"}}";
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content=new StringContent(payload) });
        });
    }
}
