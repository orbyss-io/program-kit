using System.Text.Json;
using System.Text.Json.Schema;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Orbyss.Foundation.Json;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.Web.ProblemDetails;
using Orbyss.Foundation.Web.ProblemDetails.Core;
using Numeric.Contract.Api;

var profile = new JsonProfile(new JsonProfileSettings());
var web = new JsonSerializerOptions(JsonSerializerDefaults.Web) { TypeInfoResolver = new DefaultJsonTypeInfoResolver() };
var defaultSchema = web.GetJsonSchemaAsNode(typeof(NumericRequest));
var profileSchema = JsonSchemaExporter.GetJsonSchemaAsNode(profile.TypeInfo<NumericRequest>());
var scopedSchema = web.GetJsonSchemaAsNode(typeof(StrictNumericRequest));
File.WriteAllText("aspnet-default.schema.json", defaultSchema.ToJsonString());
File.WriteAllText("foundation-profile.schema.json", profileSchema.ToJsonString());
File.WriteAllText("scoped-dto.schema.json", scopedSchema.ToJsonString());
if (profile.Deserialize<NumericRequest>("{\"amount\":12.5,\"count\":3}"u8).Amount != 12.5m)
    throw new InvalidOperationException("Numeric wire values were rejected.");
try
{
    profile.Deserialize<NumericRequest>("{\"amount\":\"12.5\",\"count\":\"3\"}"u8);
    throw new InvalidOperationException("Numeric strings were admitted.");
}
catch (JsonProfileException) { }
var sample = "{\"amount\":12.5,\"count\":3,\"amounts\":[1.25,2],\"child\":{\"revision\":4}}";
var parsed = profile.Deserialize<ScopedNumericRequest>(System.Text.Encoding.UTF8.GetBytes(sample));
if (parsed.Child.Revision != 4 || parsed.Amounts[0] != 1.25m) throw new InvalidOperationException("Nested numeric values rejected.");
foreach (var invalid in new[] {
    sample.Replace("12.5", "\"12.5\""), sample.Replace("3,", "\"3\","),
    sample.Replace("1.25", "\"1.25\""),
    sample.Replace("4}", "\"4\"}"), sample.Replace("3,", "2147483648,"),
    sample.Replace("\"count\":3", "\"count\":3,\"count\":3"),
    sample.Replace("\"count\":3", "\"count\":3,\"unexpected\":0") })
{
    try { profile.Deserialize<ScopedNumericRequest>(System.Text.Encoding.UTF8.GetBytes(invalid)); throw new InvalidOperationException("Invalid numeric token admitted."); }
    catch (JsonProfileException) { }
}
if (profile.Deserialize<ScopedNullableNumericRequest>("{\"optionalCount\":null}"u8).OptionalCount is not null ||
    profile.Deserialize<ScopedNullableNumericRequest>("{\"optionalCount\":3}"u8).OptionalCount != 3)
    throw new InvalidOperationException("Legal nullable numeric token rejected.");
try { profile.Deserialize<ScopedNullableNumericRequest>("{\"optionalCount\":\"3\"}"u8); throw new InvalidOperationException("Nullable numeric string admitted."); }
catch (JsonProfileException) { }
var response = new JsonProfile(new JsonProfileSettings { Preset = JsonProfileKeys.TolerantResponse });
File.WriteAllBytes("numeric-response.json", response.Serialize(parsed));
// Real ASP.NET producer, with no provider binding or initializer. Keep the
// Foundation reader's rejection above as the independent wire authority.
var builder = WebApplication.CreateBuilder();
builder.WebHost.UseUrls("http://127.0.0.1:0");
builder.Services.AddOpenApi("v1");
builder.Services.AddFoundationProblemDetails();
await using var app = builder.Build();
app.MapPost("/default", () => Results.NoContent()).Accepts<NumericRequest>("application/json");
app.MapPost("/scoped", () => Results.NoContent()).Accepts<StrictNumericRequest>("application/json");
app.MapGet("/problem/{status:int}", (int status) => Results.Problem(statusCode: status, detail: "Safe public detail", extensions: new Dictionary<string, object?> { ["retryMode"] = "unsafe-custom", ["statusPath"] = "/private" }));
app.MapGet("/application-problem", () => FoundationProblemResults.Problem(new ProblemDefinition(400, "invalid_input", detail: "Correct the field", fieldErrors: [new ProblemFieldError("name", "invalid", "Enter a valid name")])));
app.MapOpenApi();
await app.StartAsync();
try
{
    var address = app.Services.GetRequiredService<IServer>().Features.Get<IServerAddressesFeature>()!.Addresses.Single();
    using var client = new HttpClient();
    File.WriteAllText("producer.openapi.json", await client.GetStringAsync(address + "/openapi/v1.json"));
    foreach (var status in new[] {400, 401, 403, 500})
        File.WriteAllText($"problem-{status}.json", await client.GetStringAsyncForError(address + $"/problem/{status}"));
    File.WriteAllText("application-problem.json", await client.GetStringAsyncForError(address + "/application-problem"));
}
finally { await app.StopAsync(); }
Console.WriteLine("STRICT_NUMERIC_PROFILE_OK");

public sealed record NumericRequest(decimal Amount, int Count);
public sealed record StrictNumericRequest(
    [property: JsonNumberHandling(JsonNumberHandling.Strict)] decimal Amount,
    [property: JsonNumberHandling(JsonNumberHandling.Strict)] int Count);

public static class ErrorResponseReader
{
    public static async Task<string> GetStringAsyncForError(this HttpClient client, string url)
    {
        using var response = await client.GetAsync(url);
        if (response.IsSuccessStatusCode) throw new InvalidOperationException("Expected actual server error.");
        return await response.Content.ReadAsStringAsync();
    }
}
