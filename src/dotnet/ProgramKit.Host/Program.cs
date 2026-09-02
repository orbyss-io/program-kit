using CShells.AspNetCore.Configuration;
using CShells.AspNetCore.Extensions;
using CShells.DependencyInjection;
using Nuplane;
using Nuplane.Loading;
using Nuplane.Loading.Hosting.Builder;
using Nuplane.Sources.Directory.Configuration;
using ProgramKit.Host.Bundles;
using ProgramKit.Host.Feed;
using ProgramKit.Host.Health;
using ProgramKit.Host.Shells;
using ProgramKit.Host.Web;

if (args is ["--program-kit-healthcheck", var healthUri])
{
    using var healthClient = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
    try
    {
        using var healthResponse = await healthClient.GetAsync(healthUri).ConfigureAwait(false);
        return healthResponse.IsSuccessStatusCode ? 0 : 1;
    }
    catch (HttpRequestException)
    {
        return 1;
    }
    catch (TaskCanceledException)
    {
        return 1;
    }
}

var bootstrap = ApplicationBundleBootstrap.Prepare(args);
var environmentName = Environment.GetEnvironmentVariable("DOTNET_ENVIRONMENT")
    ?? Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT")
    ?? Environments.Production;

var builder = WebApplication.CreateBuilder(new WebApplicationOptions
{
    Args = args,
    EnvironmentName = environmentName,
    ContentRootPath = AppContext.BaseDirectory
});

// Defaults < environment defaults < bundle settings < shell structure < environment < command line.
builder.Configuration.Sources.Clear();
builder.Configuration
    .SetBasePath(AppContext.BaseDirectory)
    .AddJsonFile("appsettings.json", optional: false, reloadOnChange: false)
    .AddJsonFile($"appsettings.{environmentName}.json", optional: true, reloadOnChange: false)
    .AddJsonFile(bootstrap.HostSettingsPath, optional: true, reloadOnChange: false)
    .AddJsonFile(bootstrap.ShellsPath, optional: false, reloadOnChange: false)
    .AddInMemoryCollection(new Dictionary<string, string?>
    {
        ["ProgramKit:Bundle:Id"] = bootstrap.Manifest.BundleId,
        ["ProgramKit:Bundle:Version"] = bootstrap.Manifest.Version,
        ["ProgramKit:Bundle:Digest"] = bootstrap.Digest,
        ["ProgramKit:Bundle:Root"] = bootstrap.RootPath,
        ["Nuplane:Setup:Feeds:0:DirectoryPath"] = bootstrap.PackagesPath
    })
    .AddEnvironmentVariables()
    .AddCommandLine(args);

builder.Services.AddSingleton(bootstrap);
var configuration = builder.Configuration;
var nuplaneConfiguration = configuration.GetSection("Nuplane");

builder.Services.AddNuplane(nuplaneConfiguration, nuplane =>
{
    nuplane.AddDirectoryFeedsFromConfiguration(nuplaneConfiguration);
    nuplane.AutoloadPackages(nuplaneConfiguration.GetSection("Loading"), loading => loading
        .WithDefaultLoadMode(PackageLoadMode.HostIntegrated)
        .WithLoadModeSelectionPolicy(PackageLoadModeSelectionPolicy.ExplicitOnly)
        .SharedAssembly("CShells.Abstractions", string.Empty, 0)
        .SharedAssembly("CShells.AspNetCore.Abstractions", string.Empty, 0)
        .SharedAssembly("ProgramKit.Tasks.Abstractions", string.Empty, 0)
        .SharedAssembly("Microsoft.Extensions.DependencyInjection.Abstractions", "adb9793829ddae60", 10)
        .SharedAssembly("Microsoft.Extensions.Logging.Abstractions", "adb9793829ddae60", 10));
});
ProgramKitLoadingOptionsValidation.ReplaceNuplaneAdapter(builder.Services);

builder.Services.AddSingleton<NuplaneAssemblyProvider>();
builder.Services.AddCShellsAspNetCore(shells => shells
    .WithAssemblyProvider<NuplaneAssemblyProvider>()
    .WithConfigurationProvider(configuration)
    .WithWebRouting(options =>
    {
        options.EnablePathRouting = true;
        options.ExcludePaths = ["/health/live", "/health/ready", "/_program-kit/bundle", "/_program-kit/openapi"];
    }));

builder.Services.AddSingleton<EagerShellActivationState>();
builder.Services.AddHostedService<EagerShellActivationHostedService>();
var postgreSqlRequired = configuration.GetValue("ProgramKit:Readiness:PostgreSql:Required", false);
var postgreSqlConnectionName = configuration["ProgramKit:Readiness:PostgreSql:ConnectionStringName"];
if (postgreSqlRequired
    && (string.IsNullOrWhiteSpace(postgreSqlConnectionName)
        || string.IsNullOrWhiteSpace(configuration.GetConnectionString(postgreSqlConnectionName))))
    throw new InvalidOperationException(
        "ProgramKit:Readiness:PostgreSql requires a valid ConnectionStringName and external connection string.");
builder.Services.AddSingleton<PostgreSqlReadinessState>();
if (postgreSqlRequired)
{
    builder.Services.AddSingleton<IPostgreSqlReadinessProbe, NpgsqlPostgreSqlReadinessProbe>();
    builder.Services.AddHostedService<PostgreSqlReadinessService>();
}
builder.Services.AddProgramKitWebBoundary(configuration, builder.Environment);

var app = builder.Build();
app.UseProgramKitWebBoundary();
app.MapProgramKitHealth();
app.MapProgramKitWebBoundary();
app.MapOpenApi("/_program-kit/openapi/{documentName}.json");
app.MapShells();
app.Run();
return 0;
