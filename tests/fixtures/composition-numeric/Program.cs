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
// Real ASP.NET producer, with no provider binding or initializer. Keep the
// Foundation reader's rejection above as the independent wire authority.
var builder = WebApplication.CreateBuilder();
builder.WebHost.UseUrls("http://127.0.0.1:0");
builder.Services.AddOpenApi("v1");
await using var app = builder.Build();
app.MapPost("/default", () => Results.NoContent()).Accepts<NumericRequest>("application/json");
app.MapPost("/scoped", () => Results.NoContent()).Accepts<StrictNumericRequest>("application/json");
app.MapOpenApi();
await app.StartAsync();
try
{
    var address = app.Services.GetRequiredService<IServer>().Features.Get<IServerAddressesFeature>()!.Addresses.Single();
    using var client = new HttpClient();
    File.WriteAllText("producer.openapi.json", await client.GetStringAsync(address + "/openapi/v1.json"));
}
finally { await app.StopAsync(); }
Console.WriteLine("STRICT_NUMERIC_PROFILE_OK");

public sealed record NumericRequest(decimal Amount, int Count);
public sealed record StrictNumericRequest(
    [property: JsonNumberHandling(JsonNumberHandling.Strict)] decimal Amount,
    [property: JsonNumberHandling(JsonNumberHandling.Strict)] int Count);
