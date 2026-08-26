using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Tasks;

public static class TaskServiceCollectionExtensions
{
    public static IServiceCollection AddProgramKitStartupTask<TTask>(this IServiceCollection services)
        where TTask : class, IStartupTask
    {
        services.AddScoped<IStartupTask, TTask>();
        return services;
    }

    public static IServiceCollection AddProgramKitBackgroundTask<TTask>(this IServiceCollection services)
        where TTask : class, IBackgroundTask
    {
        services.AddSingleton<IBackgroundTask, TTask>();
        return services;
    }

    public static IServiceCollection AddProgramKitRecurringTask<TTask>(this IServiceCollection services)
        where TTask : class, IRecurringTask
    {
        services.AddSingleton<IRecurringTask, TTask>();
        return services;
    }
}
