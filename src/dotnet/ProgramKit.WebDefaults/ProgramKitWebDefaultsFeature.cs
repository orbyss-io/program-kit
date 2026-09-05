using System.Globalization;
using CShells;
using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Localization;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;

namespace ProgramKit.WebDefaults;

/// <summary>Composes Program Kit's replaceable web middleware defaults into a shell.</summary>
[ShellFeature(
    name: "ProgramKit.WebDefaults",
    DisplayName = "Program Kit Web Defaults",
    Description = "Provides localization, HSTS, correlation, and browser-security headers.")]
public sealed class ProgramKitWebDefaultsFeature(ShellSettings settings) : IMiddlewareShellFeature
{
    /// <summary>Names the correlation header emitted by the default web feature.</summary>
    public const string CorrelationHeaderName = "X-Correlation-ID";

    /// <inheritdoc />
    public int Order => -1000;

    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        services.Configure<ProgramKitWebDefaultsOptions>(
            settings.GetConfigurationRoot().GetSection("ProgramKit:Web"));
        services.AddSingleton<IValidateOptions<ProgramKitWebDefaultsOptions>, ProgramKitWebDefaultsOptionsValidator>();
        services.AddLocalization();
        services.AddOptions<RequestLocalizationOptions>()
            .Configure<IOptions<ProgramKitWebDefaultsOptions>>((options, selected) =>
            {
                var cultures = selected.Value.SupportedLocales.Select(CultureInfo.GetCultureInfo).ToArray();
                options.DefaultRequestCulture = new RequestCulture(selected.Value.DefaultLocale);
                options.SupportedCultures = cultures;
                options.SupportedUICultures = cultures;
                options.ApplyCurrentCultureToResponseHeaders = true;
            });
    }

    /// <inheritdoc />
    public void UseMiddleware(IApplicationBuilder app, IHostEnvironment? environment)
    {
        app.UseMiddleware<CorrelationAndSecurityHeadersMiddleware>();
        app.UseRequestLocalization();
        if (environment?.IsDevelopment() != true)
        {
            app.UseHsts();
        }
    }
}
