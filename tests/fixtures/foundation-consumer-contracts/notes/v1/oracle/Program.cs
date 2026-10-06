using Notes.Oracle;

if (args.Length < 1) throw new ArgumentException("Select serve or check explicitly.");
var arguments = args.Skip(1).Chunk(2).ToDictionary(pair => pair[0], pair => pair[1], StringComparer.Ordinal);
if (args[0] == "serve") await FixtureIssuer.RunAsync(arguments["--url"], arguments["--target"]);
else if (args[0] == "check")
{
    try
    {
        await NotesBehaviorOracle.RunAsync(arguments["--host"], arguments["--issuer"]);
        await File.WriteAllTextAsync("oracle-observation.json", System.Text.Json.JsonSerializer.Serialize(new { status = "passed" }));
    }
    catch (OracleAssertionException failure)
    {
        await File.WriteAllTextAsync("oracle-observation.json", System.Text.Json.JsonSerializer.Serialize(new { status = "rejected", failure.Message }));
        throw;
    }
}
else throw new ArgumentException("Unknown Notes oracle mode.");
