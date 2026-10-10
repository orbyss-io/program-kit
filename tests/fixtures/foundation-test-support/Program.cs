using System.Text.Json;
using Microsoft.Extensions.Configuration;
using ProgramKit.Foundation.TestSupport;

var output = args.Single();
using var metadata = JsonDocument.Parse("""
[{"path":"Foundation:Web:Timeout","secret":false,"binding":"native options","reload":"restart","constraints":{"minimum":1}},
 {"path":"Foundation:Web:Secret","secret":true,"binding":"secret provider","reload":"restart","constraints":{}}]
""");
var configuration = new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
    { ["Foundation:Web:Timeout"] = "3", ["Foundation:Web:Secret"] = "not-for-evidence" })
    .AddInMemoryCollection(new Dictionary<string, string?> { ["Foundation:Web:Timeout"] = "9" }).Build();
var options = new BoundOptions { Timeout = 11 }; // Actual options delegate differs from configured value.
var observations = EffectiveSettings.Capture(configuration, options, "Foundation:Web", metadata.RootElement.EnumerateArray(),
    new Dictionary<int,string> { [0] = "application", [1] = "deployment" });
Require((int)observations[0].Value! == 11 && observations[0].Sources.Single().Provider == "deployment", "Actual bound/deployment observation lost.");
Require((string)observations[1].Value! == "<redacted>", "Secret observation leaked.");
var reflective = EffectiveSettings.Capture(configuration, (object)options, "Foundation:Web", metadata.RootElement.EnumerateArray());
Require(reflective.All(setting => setting.OwnerType == typeof(BoundOptions).FullName), "Reflection observation reported System.Object rather than the activated owner type.");
Require(!JsonSerializer.Serialize(observations).Contains("not-for-evidence", StringComparison.Ordinal), "Capture retained configured secret.");
try { EffectiveSettings.Capture(configuration, options, "Foundation:Web", metadata.RootElement.EnumerateArray().Concat(metadata.RootElement.EnumerateArray())); throw new Exception("Duplicate metadata accepted."); }
catch (InvalidOperationException) { }
try { EffectiveSettings.Capture(configuration, options, "Foundation:Absent", metadata.RootElement.EnumerateArray()); throw new Exception("Absent metadata accepted."); }
catch (InvalidOperationException) { }
var invoked = 0;
var cases = new[] { new IntegrationCase("Support.actual_case", token => { token.ThrowIfCancellationRequested(); invoked++; return Task.CompletedTask; }) };
Require(await CaseSuite.RunAsync(cases, Path.Combine(output, "passed.xml")) == 0 && invoked == 1, "Executable adapter omitted actual case.");
try { await CaseSuite.RunAsync(cases, Path.Combine(output, "empty.xml"), new HashSet<string>()); throw new Exception("Empty selection accepted."); }
catch (InvalidOperationException) { }
Require(await CaseSuite.RunAsync([new("Support.actual_failure", _ => throw new Exception("not-for-evidence"))], Path.Combine(output, "failed.xml")) == 1,
    "Actual failing case accepted.");
Require(!(await File.ReadAllTextAsync(Path.Combine(output, "failed.xml"))).Contains("not-for-evidence", StringComparison.Ordinal), "Native report leaked exception secret.");
Directory.CreateDirectory(output);
await File.WriteAllTextAsync(Path.Combine(output, "observations.json"), JsonSerializer.Serialize(observations));
Console.WriteLine("Activated-value capture and executable case adapter checks passed.");
static void Require(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
/// <summary>Exercises activated operational values and forbidden secret-getter access.</summary>
sealed class BoundOptions
{
    /// <summary>The activated value intentionally differs from its configured deployment input.</summary>
    public int Timeout { get; init; }
    /// <summary>Fails if observation attempts to read protected options material.</summary>
    public string Secret => throw new InvalidOperationException("Secret getters must never be invoked.");
}
