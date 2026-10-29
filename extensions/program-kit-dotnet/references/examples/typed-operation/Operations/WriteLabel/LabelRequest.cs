using System.Text.Json.Serialization;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Wire input belongs to the API project.</summary>
[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
public sealed record LabelRequest(string Policy)
{
    /// <summary>Owns the wire admission declaration shared by registration and exported metadata.</summary>
    public static JsonContractMetadata<LabelRequest> Contract { get; } = CreateContract();

    /// <summary>Names supported capacity separately from the configured deployment budget.</summary>
    private static JsonContractMetadata<LabelRequest> CreateContract()
    {
        var profile = new JsonProfileKey("sample-label-request");
        return JsonContractFactory.Request<LabelRequest>(maximumBytes: 1024, profile: profile);
    }
}
