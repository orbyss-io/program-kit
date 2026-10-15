using LabelOwner.Core;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
var effects = 0;
app.MapPost("/labels", (LabelRequest input) =>
{
    var value = DisplayLabels.Normalize(input.Label);
    if (value is null) return Results.BadRequest(new { code = "invalid_label" });
    Interlocked.Increment(ref effects);
    return Results.Ok(new { value });
});
app.MapGet("/effects", () => Results.Ok(Volatile.Read(ref effects)));
await app.RunAsync();
