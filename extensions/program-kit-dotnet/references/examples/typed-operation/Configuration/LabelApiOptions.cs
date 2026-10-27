using System;
using CShells;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Consumer scalar options; the sample requires explicit configuration.</summary>
public sealed class LabelApiOptions
{
    /// <summary>Non-secret response prefix selected by the application's shell configuration.</summary>
    public string Prefix { get; set; } = "";

    /// <summary>Binds one owner default; missing configuration cannot silently create valid policy.</summary>
    public static void Configure(IServiceCollection services, ShellSettings settings)
    {
        var options = services.AddOptions<LabelApiOptions>();
        var configuration = settings.GetConfigurationRoot();
        var section = configuration.GetSection("Sample:Api");
        Func<LabelApiOptions, bool> valid = value => value.Prefix.Length is > 0 and <= 32;
        options
            .Bind(section)
            .Validate(valid, "Sample:Api:Prefix is required.");
    }
}
