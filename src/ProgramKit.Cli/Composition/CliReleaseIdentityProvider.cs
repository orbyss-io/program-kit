using System;
using System.Reflection;

namespace Orbyss.ProgramKit.Cli.Composition;

public static class CliReleaseIdentityProvider
{
    public const string PackageId = "Orbyss.ProgramKit.Cli";
    public const string PackageVersion = "1.0.0-alpha.1";
    public const string ToolCommandName = "program-kit";

    public static string InvokedVersion
    {
        get
        {
            string? informational = typeof(CliReleaseIdentityProvider).Assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion;
            if (string.IsNullOrWhiteSpace(informational)) return PackageVersion;
            string value = informational.Split('+', 2, StringSplitOptions.TrimEntries)[0];
            return value == "1.0.0" ? PackageVersion : value;
        }
    }
}
