using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using Orbyss.Forms;
using Orbyss.Foundation.Json;

var suite = new XElement("testsuite", new XAttribute("name", "ProgramKit.PublicComponents"));
var failed = false;
var output = Path.GetFullPath(args.Length == 1 ? args[0] : "artifacts/component-probe.xml");
await Case("immutable-public-release-and-replay", async () =>
{
    var field = new FormFieldDefinition("equipment", "/equipment", FormValueKind.String, true, Text("equipment", "Equipment"));
    var definition = new FormDefinition(new("equipment-request"), new(1), "Equipment request", "en", FormLifecycleState.Draft,
        [field], new("request", FormElementKind.VerticalLayout, [new("equipment-control", FormElementKind.Control, [], FieldId: "equipment")]), []);
    var store = new InMemoryFormReleaseStore();
    var catalog = new DefaultFormCatalogService(new InMemoryFormDefinitionStore(), store, store, new FormDefinitionValidator(), new JsonFormsCompiler());
    var created = await catalog.CreateAsync(definition, Mutation("create", null, "author"));
    var reviewed = await catalog.SubmitForReviewAsync(definition.Id, definition.Revision, ["equipment:release-probe"], Mutation("review", created.Version, "author"));
    var approved = await catalog.ApproveAsync(definition.Id, definition.Revision, Mutation("approve", reviewed.Version, "reviewer"));
    var published = await catalog.PublishAsync(definition.Id, definition.Revision, Mutation("publish", approved.Version, "publisher"));
    var replay = await catalog.PublishAsync(definition.Id, definition.Revision, Mutation("publish", approved.Version, "publisher"));
    Require(published.Value.Id.Value == "equipment-request-v1" && replay.WasReplay, "Public release/replay contract failed");
    Require(JsonSerializer.Serialize(published.Value) == JsonSerializer.Serialize(replay.Value), "Idempotent publication changed the release");
    var path = Path.Combine(Path.GetDirectoryName(output) ?? ".", "published-release.json");
    Directory.CreateDirectory(Path.GetDirectoryName(path)!);
    await File.WriteAllTextAsync(path, JsonSerializer.Serialize(published.Value, new JsonSerializerOptions(JsonSerializerDefaults.Web)));
});
await Case("explicit-strict-request-admission", () =>
{
    var profile = new JsonProfile(new JsonProfileSettings());
    var accepted = profile.Deserialize<Request>(Encoding.UTF8.GetBytes("{\"equipment\":\"camera\",\"quantity\":1}"));
    Require(accepted.Equipment == "camera" && accepted.Quantity == 1, "Typed request changed");
    foreach (var json in new[] { "{\"equipment\":\"camera\",\"quantity\":\"1\"}", "{\"equipment\":\"camera\",\"quantity\":1,\"quantity\":2}", "{\"equipment\":\"camera\",\"quantity\":1,\"extra\":true}" })
    {
        var rejected = false;
        try { profile.Deserialize<Request>(Encoding.UTF8.GetBytes(json)); }
        catch (JsonProfileException) { rejected = true; }
        Require(rejected, "Strict admission accepted incompatible input");
    }
    return Task.CompletedTask;
});
await Case("explicit-tolerant-response-admission", () =>
{
    var profile = new JsonProfile(new JsonProfileSettings { Preset = "tolerant-response" });
    var response = profile.Deserialize<Response>(Encoding.UTF8.GetBytes("{\"accepted\":true,\"futureField\":1}"));
    Require(response.Accepted, "Tolerant response lost declared behavior");
    return Task.CompletedTask;
});
Directory.CreateDirectory(Path.GetDirectoryName(output) ?? ".");
await File.WriteAllTextAsync(output, suite.ToString());
return failed ? 1 : 0;

async Task Case(string name, Func<Task> action)
{
    var test = new XElement("testcase", new XAttribute("classname", "ProgramKit.PublicComponents"), new XAttribute("name", name));
    try { await action(); }
    catch (Exception error) { failed = true; test.Add(new XElement("failure", error.ToString())); }
    suite.Add(test);
}
static LocalizedTextReference Text(string key, string fallback) => new(key, fallback);
static FormMutationContext Mutation(string key, FormConcurrencyToken? version, string actor) => new(key, version, new(actor, "fixture"), DateTimeOffset.UnixEpoch, "equipment-release");
static void Require(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
public sealed record Request(string Equipment, int Quantity);
public sealed record Response(bool Accepted);
