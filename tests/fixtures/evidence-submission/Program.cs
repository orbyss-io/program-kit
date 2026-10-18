using System.Diagnostics;
using System.Net;
using System.Net.Http.Json;
using System.Reflection;
using System.Text;
using System.Text.Json;
using CShells.AspNetCore.Configuration;
using CShells.AspNetCore.Extensions;
using CShells.AspNetCore.Resolution;
using CShells.DependencyInjection;
using CShells.Lifecycle;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.FileProviders;
using ProgramKit.Examples.Evidence;
using Evidence.Probe;

var output = Path.GetFullPath(args[0]);
var web = Path.Combine(output, "web");
var checks = new List<string>();
var configuration = new Dictionary<string, string?>();
var connection = Environment.GetEnvironmentVariable("F5_CONNECTION");
var features = new[] { "Evidence.Runtime", "Evidence.PostgreSql", "Evidence.Api", "Fixture.Identity", "Orbyss.Foundation.WebDefaults", "Orbyss.Foundation.Web.ProblemDetails", "Orbyss.Foundation.Web.OpenApi" };
foreach (var name in new[] { "desk", "invalid" })
{
    var prefix = $"CShells:Shells:{name}";
    foreach (var feature in features) configuration[$"{prefix}:Features:{feature}"] = "true";
    configuration[$"{prefix}:Configuration:WebRouting:Path"] = name;
    configuration[$"{prefix}:Configuration:Evidence:Connection"] = connection;
    configuration[$"{prefix}:Configuration:Evidence:Api:Desk"] = name == "desk" ? "Fieldwork review desk" : "";
    configuration[$"{prefix}:Configuration:Foundation:Json:Profiles:evidence-request:Preset"] = "strict-request";
    configuration[$"{prefix}:Configuration:Foundation:Json:Profiles:evidence-request:MaxBytes"] = "32768";
    configuration[$"{prefix}:Configuration:Foundation:Json:Profiles:evidence-response:Preset"] = "tolerant-response";
    configuration[$"{prefix}:Configuration:Foundation:Json:Profiles:evidence-response:MaxBytes"] = "2048";
}
var builder = WebApplication.CreateBuilder();
builder.Logging.ClearProviders();
builder.Configuration.AddInMemoryCollection(configuration);
builder.Services.AddCShellsAspNetCore(ConfigureShells);
await using var app = builder.Build();
app.Urls.Add("http://127.0.0.1:0");
var files = new PhysicalFileProvider(web);
var staticOptions = new StaticFileOptions { FileProvider = files };
app.UseStaticFiles(staticOptions);
app.MapGet("/", Index);
app.MapGet("/bff/user", User);
app.MapShells();
var registry = app.Services.GetRequiredService<IShellRegistry>();
var shell = await registry.GetOrActivateAsync("desk");
try
{
    await registry.GetOrActivateAsync("invalid");
    throw new Exception("invalid options admitted an active shell");
}
catch (Exception) when (registry.GetActive("invalid") is null) { checks.Add("invalid-options-rejected-at-shell-activation"); }
await app.StartAsync();
try
{
    await NativeChecks();
    if (args.Length > 1)
    {
        var node = Environment.GetEnvironmentVariable("F5_NODE") ?? "node";
        var browser = new ProcessStartInfo(node);
        browser.UseShellExecute = false;
        browser.CreateNoWindow = true;
        browser.RedirectStandardOutput = true;
        browser.RedirectStandardError = true;
        browser.Environment.Remove("F5_CONNECTION");
        browser.ArgumentList.Add(args[1]);
        var origin = app.Urls.Single();
        browser.ArgumentList.Add(origin);
        browser.ArgumentList.Add(output);
        var engines = args.Length > 2 ? args[2] : "chromium,webkit";
        browser.ArgumentList.Add(engines);
        using var child = Process.Start(browser)!;
        var stdout = child.StandardOutput.ReadToEndAsync();
        var stderr = child.StandardError.ReadToEndAsync();
        var limit = TimeSpan.FromSeconds(90);
        var completion = child.WaitForExitAsync();
        await completion.WaitAsync(limit);
        Console.Write(await stdout);
        Console.Error.Write(await stderr);
        Check(child.ExitCode == 0, "actual-browser-journey");
    }
    var result = new { checks, scope = "Real selected features, independent model/Core/application/HTTP and optional browser; fictional identity, no provider login or durability beyond this PostgreSQL fixture." };
    var serialized = JsonSerializer.Serialize(result);
    var resultPath = Path.Combine(output, "native-result.json");
    await File.WriteAllTextAsync(resultPath, serialized);
    Console.WriteLine(serialized);
}
finally { await app.StopAsync(); files.Dispose(); }

void ConfigureShells(CShellsBuilder shells)
{
    Assembly[] assemblies = [typeof(EvidenceApiFeature).Assembly, typeof(EvidenceProviderFeature).Assembly, typeof(EvidenceRuntimeFeature).Assembly, typeof(Program).Assembly,
        typeof(Orbyss.Foundation.WebDefaults.FoundationWebDefaultsFeature).Assembly,
        typeof(Orbyss.Foundation.Web.ProblemDetails.FoundationProblemDetailsFeature).Assembly,
        typeof(Orbyss.Foundation.Web.OpenApi.FoundationOpenApiFeature).Assembly];
    shells
        .WithAssemblies(assemblies)
        .WithConfigurationProvider(builder.Configuration)
        .WithWebRouting(ConfigureRouting);
}
void ConfigureRouting(WebRoutingShellResolverOptions options) => options.EnablePathRouting = true;
IResult Index()
{
    var path = Path.Combine(web, "index.html");
    return Results.File(path, "text/html");
}
IResult User()
{
    var projection = new { authenticated = true };
    return Results.Json(projection);
}
void Check(bool condition, string identity)
{
    if (!condition) throw new InvalidOperationException(identity);
    checks.Add(identity);
}

async Task NativeChecks()
{
    await ApplicationContractChecks.VerifyAsync();
    checks.Add("pure-application-client-admission-and-substitution");
    var bytes = Encoding.UTF8.GetBytes("fictional evidence");
    var date = new DateOnly(
        2026,
        10,
        18
    );
    var caseTitle = Environment.GetEnvironmentVariable("F5_CASE_LABEL") ?? "Native evidence";
    var packet = EvidencePacket.Create(
        caseTitle,
        date,
        bytes
    );
    bytes[0] = 0;
    var copied = packet.CopyContent();
    copied[1] = 0;
    var retained = packet.CopyContent();
    Check(retained[0] == 102 && retained[1] == 105, "immutable-construction-copies-input-and-output");
    var cacheOptions = new MemoryCacheOptions();
    using var cache = new MemoryCache(cacheOptions);
    cache.Set("packet", packet);
    var cached = cache.Get<EvidencePacket>("packet")!;
    var cachedBytes = cached.CopyContent();
    Check(cachedBytes[0] == 102, "cached-value-does-not-expose-owned-buffer");
    foreach (var title in new[] { "", "\u0001private" })
    {
        try
        {
            EvidencePacket.Create(
                title,
                date,
                retained
            );
            throw new Exception("invalid-construction-admitted");
        }
        catch (ArgumentException) { checks.Add("invalid-construction-rejected"); }
    }
    var document = Encoding.UTF8.GetBytes("{\"desk\":\"Private fictional desk\"}");
    using var input = new MemoryStream(document);
    var deployment = await ReviewDeploymentLoader.LoadAsync(input, CancellationToken.None);
    Check(deployment.Desk == "Private fictional desk" && input.CanRead, "explicit-loader-preserves-caller-stream-ownership");
    var excess = new byte[1025];
    using var oversized = new MemoryStream(excess);
    try { await ReviewDeploymentLoader.LoadAsync(oversized, CancellationToken.None); throw new Exception("unbounded-loader"); }
    catch (InvalidDataException) { checks.Add("loader-bound-rejected"); }
    using var scope = shell!.ServiceProvider.CreateScope();
    var application = scope.ServiceProvider.GetService<IEvidenceSubmissions>();
    Check(application is not null, "actual-runtime-registration");
    var database = scope.ServiceProvider.GetRequiredService<EvidenceDbContext>();
    using (var second = shell.ServiceProvider.CreateScope())
    {
        var other = second.ServiceProvider.GetRequiredService<IEvidenceSubmissions>();
        var otherDatabase = second.ServiceProvider.GetRequiredService<EvidenceDbContext>();
        var separateScopes = !ReferenceEquals(application, other) && !ReferenceEquals(database, otherDatabase);
        Check(separateScopes, "actual-feature-request-scopes-are-independent");
    }
    var acceptedPath = Path.Combine(output, "accepted-model.json");
    var acceptedBytes = await File.ReadAllBytesAsync(acceptedPath);
    using var accepted = JsonDocument.Parse(acceptedBytes);
    var authority = accepted.RootElement;
    var entities = database.Model.GetEntityTypes();
    var model = entities.Single();
    var table = model.GetTableName()!;
    var schema = model.GetSchema();
    var expectedTableProperty = authority.GetProperty("table");
    var expectedTable = expectedTableProperty.GetString();
    var expectedSchemaProperty = authority.GetProperty("schema");
    var expectedSchema = expectedSchemaProperty.GetString();
    Check(table == expectedTable && schema == expectedSchema, "independent-accepted-table-authority");
    var store = StoreObjectIdentifier.Table(table, schema);
    var properties = model.GetProperties();
    Func<IProperty, string> columnName = property => property.GetColumnName(store)!;
    Func<IProperty, string?> columnType = property => property.GetColumnType();
    var actualColumns = properties.ToDictionary(columnName, columnType);
    var expectedColumnProperty = authority.GetProperty("columns");
    var expectedColumns = expectedColumnProperty.EnumerateObject();
    Func<JsonProperty, bool> matches = property => actualColumns[property.Name] == property.Value.GetString();
    var columnsMatch = actualColumns.Count == 5 && expectedColumns.All(matches);
    Check(columnsMatch, "independent-accepted-column-authority");
    var primaryKey = model.FindPrimaryKey()!;
    var keyProperty = primaryKey.Properties.Single();
    var key = keyProperty.GetColumnName(store);
    Check(key == "identity", "independent-key-authority");
    var concurrencyProperty = properties.Single(property => property.IsConcurrencyToken);
    var concurrency = concurrencyProperty.GetColumnName(store);
    Check(concurrency == "revision", "independent-concurrency-authority");
    var prepared = await application!.PrepareAsync(
        "fictional-reviewer",
        packet,
        CancellationToken.None
    );
    Check(!prepared.Accepted, "business-preparation-independent-of-http");
    var denied = await application.FindAsync(
        "other-reviewer",
        prepared.Id,
        CancellationToken.None
    );
    Check(denied is null, "provider-owner-query-isolation");
    var receipt = await application.AcceptAsync(
        "fictional-reviewer",
        prepared.Id,
        CancellationToken.None
    );
    Check(receipt?.Accepted == true && receipt.Hash == packet.Hash, "actual-provider-json-and-business-acceptance");
    await application.AcceptAsync(
        "fictional-reviewer",
        prepared.Id,
        CancellationToken.None
    );
    var origin = app.Urls.Single();
    var address = new Uri(origin);
    using var client = new HttpClient { BaseAddress = address };
    var openapi = await client.GetStringAsync("/desk/_orbyss-foundation/openapi/v1.json");
    var documentPath = Path.Combine(output, "evidence.openapi.json");
    await File.WriteAllTextAsync(documentPath, openapi);
    var location = "/desk/api/evidence/" + prepared.Id;
    using var anonymous = await client.GetAsync(location);
    Check(anonymous.StatusCode == HttpStatusCode.Unauthorized, "real-http-admission-denial");
    var denialHeaders = anonymous.Headers.Contains("X-Frame-Options");
    Check(denialHeaders, "native-headers-cover-denial");
    client.DefaultRequestHeaders.Add("X-Fixture-Owner", "fictional-reviewer");
    using var observed = await client.GetAsync(location);
    var result = await observed.Content.ReadFromJsonAsync<EvidenceResponse>();
    Check(observed.IsSuccessStatusCode && result!.Accepted && result.Desk == "Fieldwork review desk", "real-http-mapping-and-nondefault-options");
    var successHeaders = observed.Headers.Contains("X-Correlation-ID") && observed.Headers.CacheControl!.NoStore;
    Check(successHeaders, "native-middleware-success-scope");
    var invalidPayload = "{\"title\":\"x\",\"date\":\"2026-10-18\",\"content\":\"eA==\",\"extra\":true}";
    var invalidJson = new StringContent(
        invalidPayload,
        Encoding.UTF8,
        "application/json"
    );
    using var invalid = await client.PostAsync("/desk/api/evidence", invalidJson);
    Check(invalid.StatusCode == HttpStatusCode.BadRequest, "native-strict-json-admission");
    var failureHeaders = invalid.Headers.Contains("X-Frame-Options");
    Check(failureHeaders, "native-headers-cover-fault");
    var oversizedPayload = new string(' ', 32769);
    using var oversizedJson = new StringContent(
        oversizedPayload,
        Encoding.UTF8,
        "application/json"
    );
    using var oversizedResponse = await client.PostAsync("/desk/api/evidence", oversizedJson);
    Check((int)oversizedResponse.StatusCode == 413, "actual-http-wire-byte-bound");
    foreach (var invalidInput in new[]
    {
        "{\"title\":\"Date control\",\"date\":\"invalid\",\"content\":\"eA==\"}",
        "{\"title\":\"Content control\",\"date\":\"2026-10-18\",\"content\":\"invalid base64!\"}",
        "{\"title\":\"\",\"date\":\"2026-10-18\",\"content\":\"eA==\"}"
    })
    {
        using var inputJson = new StringContent(
            invalidInput,
            Encoding.UTF8,
            "application/json"
        );
        using var inputResponse = await client.PostAsync("/desk/api/evidence", inputJson);
        var mediaType = inputResponse.Content.Headers.ContentType?.MediaType;
        Check(inputResponse.StatusCode == HttpStatusCode.BadRequest && mediaType == "application/problem+json", "transport-invalid-input-is-client-problem");
    }
    client.DefaultRequestHeaders.Remove("X-Fixture-Owner");
    client.DefaultRequestHeaders.Add("X-Fixture-Owner", "other-reviewer");
    using var foreign = await client.GetAsync(location);
    var foreignStatus = (int)foreign.StatusCode;
    Check(foreign.StatusCode == HttpStatusCode.NotFound, $"http-does-not-disclose-other-owner-receipt:{foreignStatus}");
    var disposed = database;
    scope.Dispose();
    try { _ = disposed.Database; throw new Exception("disposed-context-remained-usable"); }
    catch (ObjectDisposedException) { checks.Add("actual-provider-scope-disposal"); }
}
