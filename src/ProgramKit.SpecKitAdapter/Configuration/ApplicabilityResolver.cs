using System;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;

namespace Orbyss.ProgramKit.SpecKitAdapter.Configuration;

public sealed record ApplicabilityResolution(ActivationMode Mode, Applicability Applicability, bool Active, bool BlocksWorkflow, string Source);

public static class ApplicabilityResolver
{
    public static ApplicabilityResolution Resolve(JsonObject config, string featureKey)
    {
        JsonObject activation = config["activation"]!.AsObject();
        ActivationMode defaultMode = ParseMode(activation["defaultMode"]!.GetValue<string>());
        JsonObject features = activation["features"]!.AsObject();
        if (features[featureKey] is not JsonObject feature)
        {
            bool blocks = defaultMode == ActivationMode.Required;
            return new ApplicabilityResolution(defaultMode, Applicability.Unresolved, Active: false, BlocksWorkflow: blocks, "project-default");
        }

        bool hasModeOverride = feature["mode"] is not null;
        ActivationMode mode = hasModeOverride ? ParseMode(feature["mode"]!.GetValue<string>()) : defaultMode;
        Applicability applicability = ParseApplicability(feature["applicability"]!.GetValue<string>());
        bool active = mode != ActivationMode.Off && applicability == Applicability.Applicable;
        bool blocking = mode == ActivationMode.Required && applicability == Applicability.Unresolved;
        return new ApplicabilityResolution(mode, applicability, active, blocking, hasModeOverride ? "feature-override" : "project-default");
    }

    private static ActivationMode ParseMode(string value) => value switch
    {
        "off" => ActivationMode.Off,
        "assist" => ActivationMode.Assist,
        "required" => ActivationMode.Required,
        _ => throw new ArgumentOutOfRangeException(nameof(value)),
    };

    private static Applicability ParseApplicability(string value) => value switch
    {
        "applicable" => Applicability.Applicable,
        "disabled" => Applicability.Disabled,
        "not-applicable" => Applicability.NotApplicable,
        "unresolved" => Applicability.Unresolved,
        _ => throw new ArgumentOutOfRangeException(nameof(value)),
    };
}
