using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace Activation.Tests;

public sealed class SelectedFeatureTests
{
    [Fact]
    public async Task GeneratedFeatureExposesContractsAndRegistersWithoutProviderWork()
    {
        var feature = new Activation.Api.ApiFeature();
        Assert.IsAssignableFrom<IShellFeature>(feature);
        var webFeature = Assert.IsAssignableFrom<IWebShellFeature>(feature);
        var services = new ServiceCollection();
        feature.ConfigureServices(services);
        Assert.Empty(services);
        await using var provider = services.BuildServiceProvider(new ServiceProviderOptions
        {
            ValidateScopes = true,
            ValidateOnBuild = true
        });
        var builder = WebApplication.CreateBuilder();
        await using var application = builder.Build();
        webFeature.MapEndpoints(application, application.Environment);
        Assert.Empty(((IEndpointRouteBuilder)application).DataSources);
    }
}
