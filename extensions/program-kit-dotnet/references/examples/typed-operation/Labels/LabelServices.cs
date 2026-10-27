using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.Execution;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Called by the owning runtime feature; does not activate or resolve a provider.</summary>
public static class LabelServices
{
    /// <summary>Registers the application's scoped label capability.</summary>
    public static void Configure(IServiceCollection services, IConfiguration configuration)
    {
        services.AddFoundationExecution();
        var section = configuration.GetSection("Sample:Execution");
        var options = services.AddOptions<LabelExecutionOptions>();
        Func<LabelExecutionOptions, bool> valid = value => value.Timeout > TimeSpan.Zero
            && value.Timeout.TotalMilliseconds <= uint.MaxValue - 1d;
        options
            .Bind(section)
            .Validate(valid, "Sample:Execution:Timeout must be a supported positive duration.");
        services.AddScoped<ILabelOperations, LabelOperations>();
    }
}
