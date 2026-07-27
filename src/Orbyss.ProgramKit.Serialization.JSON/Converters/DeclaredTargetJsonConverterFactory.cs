using System.Collections.Immutable;
using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Converters;

internal sealed class DeclaredTargetJsonConverterFactory : JsonConverterFactory
{
    private readonly JsonConverterFactory factory;
    private readonly ImmutableHashSet<Type> acceptedRuntimeTargets;
    private readonly string ownerIdentity;

    internal DeclaredTargetJsonConverterFactory(
        JsonConverterFactory factory,
        ImmutableHashSet<Type> acceptedRuntimeTargets,
        string ownerIdentity)
    {
        ArgumentNullException.ThrowIfNull(factory);
        ArgumentNullException.ThrowIfNull(acceptedRuntimeTargets);
        ArgumentException.ThrowIfNullOrWhiteSpace(ownerIdentity);
        this.factory = factory;
        this.acceptedRuntimeTargets = acceptedRuntimeTargets;
        this.ownerIdentity = ownerIdentity;
    }

    public override bool CanConvert(Type typeToConvert) =>
        acceptedRuntimeTargets.Contains(typeToConvert);

    public override JsonConverter CreateConverter(
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (!acceptedRuntimeTargets.Contains(typeToConvert))
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                $"Converter factory '{ownerIdentity}' was invoked for an undeclared or unaccepted target '{typeToConvert.FullName}'.",
                "/targetTypeFamilies");
        }

        try
        {
            var converter = factory.CreateConverter(typeToConvert, options)
                ?? throw ProgramKitJsonException.Create(
                    ProgramKitJsonDiagnosticIds.InvalidContribution,
                    $"Converter factory '{ownerIdentity}' returned no converter for '{typeToConvert.FullName}'.",
                    "/targetTypeFamilies");
            return ExactDecimalStringConverterPolicy.Apply(
                typeToConvert,
                converter);
        }
        catch (ProgramKitJsonException)
        {
            throw;
        }
        catch (Exception exception) when (JsonExceptionBoundary.IsNonFatal(exception))
        {
            throw new ProgramKitJsonException(
                new ProgramKitDiagnostic(
                    ProgramKitJsonDiagnosticIds.InvalidContribution,
                    ProgramKitDiagnosticSeverity.Error,
                    $"Converter factory '{ownerIdentity}' failed for declared target '{typeToConvert.FullName}'.",
                    "/targetTypeFamilies"),
                exception);
        }
    }
}
