using CShells.AspNetCore.Configuration;
using CShells.AspNetCore.Extensions;
using CShells.DependencyInjection;
using Nuplane;
using Nuplane.Loading.Hosting.Builder;
using Nuplane.Sources.Directory.Configuration;
using ProgramKit.Host.Bundles;
using ProgramKit.Host.Feed;
using ProgramKit.Host.Health;
using ProgramKit.Host.Shells;

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
    nuplane.AutoloadPackages(nuplaneConfiguration.GetSection("Loading"));
});

builder.Services.AddSingleton<NuplaneAssemblyProvider>();
builder.Services.AddCShellsAspNetCore(shells => shells
    .WithAssemblyProvider<NuplaneAssemblyProvider>()
    .WithConfigurationProvider(configuration)
    .WithWebRouting(options =>
    {
        options.EnablePathRouting = true;
        options.ExcludePaths = ["/health/live", "/health/ready", "/_program-kit/bundle"];
    }));

builder.Services.AddHostedService<EagerShellActivationHostedService>();

var app = builder.Build();
app.MapProgramKitHealth();
app.MapShells();
app.Run();
