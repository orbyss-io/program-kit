using System;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Providers;

namespace Orbyss.ProgramKit.Providers.DotNet.Manifests;

public static class DotNetProviderManifest
{
    public const string StableKey = "orbyss.program-kit.dotnet:factory-provider:dotnet-cshells@1.0.0";
    public const string Profile = "dotnet10-cshells-0.0.28";

    public static ProviderManifest Create()
    {
        string digest = $"sha256:{Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes("dotnet10-cshells-0.0.28@29fe542835696131278fcacc6cdb9a6186fc0447"))).ToLowerInvariant()}";
        return new ProviderManifest(
            new GovernedIdentity("orbyss.program-kit.dotnet", "factory-provider", "dotnet-cshells", "1.0.0", digest),
            new GovernedIdentity("orbyss.program-kit.dotnet", "distribution", "dotnet10-cshells", "1.0.0", digest),
            new[] { ProviderRole.IntakeMapping, ProviderRole.Construction, ProviderRole.Evaluation },
            new[] { Profile },
            new[] { "program-kit.software-definition-bundle/v1", "program-kit.provider.dotnet.component-api-definition/v1" },
            new[] { "dotnet-component-package", "aspnetcore-application" },
            new[] { "dotnet restore", "dotnet build", "dotnet pack" },
            new[] { "read-workspace", "write-candidate", "write-local-package-source" });
    }
}
