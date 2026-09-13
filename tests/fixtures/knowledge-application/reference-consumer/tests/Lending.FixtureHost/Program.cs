using System.Text.Json;
using System.Text.Json.Serialization;
using Lending.Core;
using Lending.Storage;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<ILendingStore>(new FileLendingStore(Environment.GetEnvironmentVariable("LENDING_FIXTURE_DATA") ?? throw new InvalidOperationException("Fixture data directory required")));
builder.Services.AddSingleton<Reservations>();
builder.Services.AddSingleton<IReservationIdentity, RandomIdentity>();
var app = builder.Build();
var strict = new JsonSerializerOptions(JsonSerializerDefaults.Web) { UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow, PropertyNameCaseInsensitive = false, NumberHandling = JsonNumberHandling.Strict };
var webRoot = Environment.GetEnvironmentVariable("LENDING_FIXTURE_WEB");
if (webRoot is not null)
{
    app.MapGet("/", () => Results.File(Path.Combine(webRoot, "index.html"), "text/html"));
    app.MapGet("/app.js", () => Results.File(Path.Combine(webRoot, "app.js"), "application/javascript"));
}
app.MapPost("/api/v1/reservations", async (HttpRequest request, Reservations reservations) =>
{
    var input = await Admit<ReserveV1>(request);
    return input is null || input.Quantity <= 0 ? Results.BadRequest() : Response(reservations.Reserve(input.OperationId, input.EquipmentId, input.Quantity));
});
app.MapPost("/api/v1/reservations/{id}/confirm", async (string id, HttpRequest request, Reservations reservations) =>
{
    var input = await Admit<ConfirmV1>(request);
    return input is null ? Results.BadRequest() : Response(reservations.Transition(id, input.OperationId, true, input.Acknowledged));
});
app.MapPost("/api/v1/reservations/{id}/cancel", async (string id, HttpRequest request, Reservations reservations) =>
{
    var input = await Admit<CancelV1>(request);
    return input is null ? Results.BadRequest() : Response(reservations.Transition(id, input.OperationId, false, true));
});
app.MapGet("/api/v1/reservations/{id}", (string id, ILendingStore store) => store.InTransaction(s => s.Reservations.TryGetValue(id, out var value) ? Results.Json(Wire(value)) : Results.NotFound()));
if (app.Environment.IsEnvironment("ProgramKitAcceptanceFixture"))
{
    app.MapGet("/__acceptance/snapshot", (ILendingStore store) => store.InTransaction(s => Results.Json(new { s.Available, Reservations = s.Reservations.ToDictionary(x => x.Key, x => Wire(x.Value)), s.NotificationAttempts, s.NotificationsSent, s.PendingNotifications })));
    app.MapPost("/__acceptance/reset", (ILendingStore store) => store.InTransaction(s => { s.Available = 2; s.Reservations.Clear(); s.Operations.Clear(); s.NotificationAttempts = s.NotificationsSent = s.PendingNotifications = 0; s.FailNext = false; return Results.Json(new { reset = true }); }));
    app.MapPost("/__acceptance/fail-next-notification", (ILendingStore store) => store.InTransaction(s => { s.FailNext = true; return Results.Json(new { armed = true }); }));
    app.MapPost("/__acceptance/drain-notifications", (ILendingStore store) => store.InTransaction(s => { s.NotificationAttempts += s.PendingNotifications; s.NotificationsSent += s.PendingNotifications; s.PendingNotifications = 0; return Results.Json(new { drained = true }); }));
}
app.Run();

async Task<T?> Admit<T>(HttpRequest request) where T : AdmissionV1
{
    try
    {
        using var document = await JsonDocument.ParseAsync(request.Body);
        if (document.RootElement.ValueKind != JsonValueKind.Object) return null;
        var names = document.RootElement.EnumerateObject().Select(p => p.Name).ToArray();
        if (names.Distinct(StringComparer.Ordinal).Count() != names.Length) return null;
        var value = document.RootElement.Deserialize<T>(strict);
        return value is null || string.IsNullOrWhiteSpace(value.OperationId) ? null : value;
    }
    catch (JsonException) { return null; }
}
static object Wire(Reservation value) => new { value.ReservationId, value.OperationId, value.EquipmentId, value.Quantity, State = value.State.ToString() };
static IResult Response(Outcome value) => Results.Json(value.Reservation is null ? null : Wire(value.Reservation), statusCode: value.Decision switch { Decision.Created => 201, Decision.Invalid => 400, Decision.Denied => 409, Decision.DurablePending => 202, _ => 200 });
abstract record AdmissionV1(string OperationId);
sealed record ReserveV1(string OperationId, string EquipmentId, int Quantity) : AdmissionV1(OperationId);
sealed record ConfirmV1(string OperationId, bool Acknowledged) : AdmissionV1(OperationId);
sealed record CancelV1(string OperationId) : AdmissionV1(OperationId);
sealed class RandomIdentity : IReservationIdentity { public string Next() => Guid.NewGuid().ToString("N"); }
