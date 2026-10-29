using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>The stored sample resource's wire representation belongs to the API project.</summary>
public sealed record LabelResponse(string Policy)
{
    /// <summary>Both operations publish and register this same shared wire definition.</summary>
    public static JsonContractMetadata<LabelResponse> Contract { get; } = CreateContract();

    /// <summary>Declares supported capacity without choosing the shell's actual budget.</summary>
    private static JsonContractMetadata<LabelResponse> CreateContract()
    {
        var profile = new JsonProfileKey("sample-label-response");
        return JsonContractFactory.Response<LabelResponse>(maximumBytes: 2048, profile: profile);
    }
}
