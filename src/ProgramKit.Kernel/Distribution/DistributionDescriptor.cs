using System;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Distribution;

public static class DistributionDescriptor
{
    public const string PackageId = "Orbyss.ProgramKit.Cli";
    public const string Version = "1.0.0-alpha.2";
    public const string CommandName = "program-kit";

    public static JsonObject ValidateBinding(JsonObject binding)
    {
        StructuralSchemaValidator validator = new(new SchemaRegistry());
        var failures = validator.Validate(Orbyss.ProgramKit.Contracts.Schemas.ContractSchemaResources.DistributionBindingId, binding);
        if (failures.Count > 0) throw new InvalidDataException(string.Join(" | ", failures));
        if (!string.Equals(binding["packageId"]!.GetValue<string>(), PackageId, StringComparison.Ordinal)
            || !string.Equals(binding["packageVersion"]!.GetValue<string>(), Version, StringComparison.Ordinal)
            || !string.Equals(binding["reportedVersion"]!.GetValue<string>(), Version, StringComparison.Ordinal)
            || !string.Equals(binding["commandName"]!.GetValue<string>(), CommandName, StringComparison.Ordinal))
        {
            throw new InvalidDataException("The request distribution does not match this exact Program Kit release.");
        }

        return (JsonObject)binding.DeepClone();
    }
}
