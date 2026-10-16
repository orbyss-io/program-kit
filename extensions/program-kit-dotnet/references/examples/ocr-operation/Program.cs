using System.Net;
using System.Security.Cryptography;
using System.Text.Json;
using ProgramKit.Examples.Ocr;

if (args is ["ticket",var ticketPath,var ticketSha256])
{
    await NativeWorker.RunAsync(ticketPath,ticketSha256);
    return;
}
if (args is not ["recording-tests"])
    throw new ArgumentException("Expected recording-tests or one exact consumed engine ticket.");
var cases = new List<string>();
var endpoint = new Uri("https://fictional-account.cognitiveservices.azure.com/");
var document = System.Text.Encoding.ASCII.GetBytes("%PDF-1.4\n%synthetic envelope only; no PDF validity or provider claim\n%%EOF");
var digest = Convert.ToHexStringLower(SHA256.HashData(document));
var operationId = Guid.NewGuid().ToString("D");
HttpResponseMessage Accepted(string? location = null, string content = "{}")
{
    var response = new HttpResponseMessage(HttpStatusCode.Accepted) { Content = new StringContent(content) };
    response.Headers.TryAddWithoutValidation("Operation-Location",location ?? endpoint+"documentintelligence/documentModels/prebuilt-read/analyzeResults/"+operationId+"?api-version=2024-11-30");
    return response;
}
void Require(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}
async Task Execute(string name, Func<Task> run)
{
    await run();
    cases.Add(name);
}
await Execute("native-started-one-page-read-exact-envelope-no-implicit-poll",async () =>
{
    var envelope = new OcrEnvelope(endpoint,document,digest,1024,32768);
    string? retained = null;
    var terminal = new RecordingTerminal((_,_) => Task.FromResult(Accepted()));
    using var gate = new OcrSubmissionHandler(envelope,value => retained=value) { InnerHandler=terminal };
    using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(5));
    await NativeOcrSubmission.SubmitAsync(envelope,"fictional-key",gate,deadline.Token);
    Require(terminal.Calls==1 && gate.ObservedSubmissions==1 && retained==operationId,"native request or acknowledgement contract changed");
});
await Execute("native-envelope-owns-input-copy",async () =>
{
    var input = document.ToArray();
    var envelope = new OcrEnvelope(endpoint,input,digest,1024,32768);
    input[0]^=1;
    var terminal = new RecordingTerminal((_,_) => Task.FromResult(Accepted()));
    using var gate = new OcrSubmissionHandler(envelope,_ => {}) { InnerHandler=terminal };
    await NativeOcrSubmission.SubmitAsync(envelope,"fictional-key",gate,CancellationToken.None);
    Require(terminal.Calls==1,"caller mutation changed the owned native input");
});
foreach (var status in new[] { HttpStatusCode.TooManyRequests,HttpStatusCode.ServiceUnavailable })
    await Execute("native-no-sdk-retry-"+(int)status,async () =>
    {
        var envelope = new OcrEnvelope(endpoint,document,digest,1024,32768);
        var terminal = new RecordingTerminal((_,_) => Task.FromResult(new HttpResponseMessage(status) { Content=new StringContent("{}") }));
        using var gate = new OcrSubmissionHandler(envelope,_ => {}) { InnerHandler=terminal };
        var failed=false;
        try { await NativeOcrSubmission.SubmitAsync(envelope,"fictional-key",gate,CancellationToken.None); }
        catch (Azure.RequestFailedException) { failed=true; }
        Require(failed && terminal.Calls==1 && gate.ObservedSubmissions==1,"SDK retried a failed paid-shaped request");
    });
await Execute("native-physical-second-submit-denied",async () =>
{
    var envelope = new OcrEnvelope(endpoint,document,digest,1024,32768);
    var terminal = new RecordingTerminal((_,_) => Task.FromResult(Accepted()));
    using var gate = new OcrSubmissionHandler(envelope,_ => {}) { InnerHandler=terminal };
    await NativeOcrSubmission.SubmitAsync(envelope,"fictional-key",gate,CancellationToken.None);
    var failed=false;
    try { await NativeOcrSubmission.SubmitAsync(envelope,"fictional-key",gate,CancellationToken.None); }
    catch (InvalidOperationException) { failed=true; }
    Require(failed && terminal.Calls==1,"a reused native handler reached the terminal twice");
});
foreach (var (name,location) in new[] {
    ("foreign-origin","https://foreign.invalid/documentintelligence/documentModels/prebuilt-read/analyzeResults/"+operationId+"?api-version=2024-11-30"),
    ("foreign-model",endpoint+"documentintelligence/documentModels/prebuilt-invoice/analyzeResults/"+operationId+"?api-version=2024-11-30"),
    ("malformed-handle",endpoint+"documentintelligence/documentModels/prebuilt-read/analyzeResults/not-an-owned-guid?api-version=2024-11-30") })
    await Execute("native-unowned-acknowledgement-"+name,async () =>
    {
        var envelope = new OcrEnvelope(endpoint,document,digest,1024,32768);
        var terminal = new RecordingTerminal((_,_) => Task.FromResult(Accepted(location)));
        var retained=false;
        using var gate = new OcrSubmissionHandler(envelope,_ => retained=true) { InnerHandler=terminal };
        var failed=false;
        try { await NativeOcrSubmission.SubmitAsync(envelope,"fictional-key",gate,CancellationToken.None); }
        catch (InvalidDataException) { failed=true; }
        Require(failed && terminal.Calls==1 && !retained,"foreign acknowledgement became an owned handle");
    });
await Execute("native-retain-handle-before-bounded-response-failure",async () =>
{
    var envelope = new OcrEnvelope(endpoint,document,digest,1024,64);
    var terminal = new RecordingTerminal((_,_) => Task.FromResult(Accepted(content:new string('x',65))));
    string? retained=null;
    using var gate = new OcrSubmissionHandler(envelope,value => retained=value) { InnerHandler=terminal };
    var failed=false;
    try { await NativeOcrSubmission.SubmitAsync(envelope,"fictional-key",gate,CancellationToken.None); }
    catch (Azure.RequestFailedException error) when (error.InnerException is HttpRequestException) { failed=true; }
    Require(failed && terminal.Calls==1 && retained==operationId,"known handle was lost after response work failed");
});
await Execute("native-cancellation-before-dispatch-zero-terminal-calls",async () =>
{
    var envelope = new OcrEnvelope(endpoint,document,digest,1024,32768);
    var terminal = new RecordingTerminal((_,_) => Task.FromResult(Accepted()));
    using var gate = new OcrSubmissionHandler(envelope,_ => {}) { InnerHandler=terminal };
    using var canceled=new CancellationTokenSource();canceled.Cancel();
    var failed=false;
    try { await NativeOcrSubmission.SubmitAsync(envelope,"fictional-key",gate,canceled.Token); }
    catch (OperationCanceledException) { failed=true; }
    Require(failed && terminal.Calls==0,"canceled native request reached the terminal");
});
Console.WriteLine(JsonSerializer.Serialize(new { status="passed",scope="actual public SDK with offline recording HTTP only",cases,
    providerCalls=0,modelCalls=0,providerAcceptance=false }));
