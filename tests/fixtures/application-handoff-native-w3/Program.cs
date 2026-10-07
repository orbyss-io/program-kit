using System.Security.Cryptography;
using System.Text.Json;

// This pure exporter constructs only its typed settings value. It does not create a host,
// register services, run hosted services, resolve storage or contact identity providers.
if (args is ["self-test"])
{
    if (new ApplicationSettings().Capacity != ApplicationSettings.DefaultCapacity
        || !ApplicationSettings.IsValid(1) || !ApplicationSettings.IsValid(8)
        || ApplicationSettings.IsValid(0) || ApplicationSettings.IsValid(9))
        throw new InvalidOperationException("Typed setting defaults/validation diverged.");
    Console.WriteLine("Typed application settings acceptance passed without initialization.");
    return;
}
if (args is not ["metadata", var sourcePath])
    throw new ArgumentException("Use metadata <owning-source> or self-test.");
var source = File.ReadAllBytes(sourcePath);
var hash = Convert.ToHexStringLower(SHA256.HashData(source));
var settings = new ApplicationSettings();
var metadata = new
{
    schemaVersion = 1,
    owner = "PublishedTools.Contract.Api",
    scope = "application-settings",
    complete = true,
    sources = new Dictionary<string, string> { ["src/SettingsExporter/Program.cs"] = hash },
    settings = new object[]
    {
        new
        {
            path = "Application:Capacity", type = "integer", required = false, secret = false,
            @default = settings.Capacity,
            constraints = new { minimum = ApplicationSettings.MinimumCapacity, maximum = ApplicationSettings.MaximumCapacity },
            binding = "Application-owned typed construction; this fixture does not claim framework binder coverage.",
            precedence = new[] { "Typed application default; explicit application arguments may select a validated value." },
            reload = "restart", description = "Admitted capacity of the stateless application specimen."
        }
    },
    semanticConstraints = new[] { "ApplicationSettings.IsValid owns the inclusive capacity range." }
};
Console.WriteLine(JsonSerializer.Serialize(metadata));

sealed class ApplicationSettings
{
    public const int DefaultCapacity = 2;
    public const int MinimumCapacity = 1;
    public const int MaximumCapacity = 8;
    public int Capacity { get; init; } = DefaultCapacity;
    public static bool IsValid(int value) => value is >= MinimumCapacity and <= MaximumCapacity;
}
