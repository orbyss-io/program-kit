using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Quality.Diagnostics;
using Orbyss.ProgramKit.Quality.Execution;
using Orbyss.ProgramKit.Quality.Specifications;

namespace Orbyss.ProgramKit.Quality.Validation;

/// <summary>Validates that an exact specification/profile selection satisfies execution requirements.</summary>
public sealed class TestExecutionSelectionValidator : ITestExecutionSelectionValidator
{
    private readonly IProgramKitSemanticValidator<TestSpecification> _specificationValidator;
    private readonly IProgramKitSemanticValidator<ExecutionProfile> _profileValidator;

    /// <summary>Creates a selection validator with explicit semantic dependencies.</summary>
    public TestExecutionSelectionValidator(
        IProgramKitSemanticValidator<TestSpecification> specificationValidator,
        IProgramKitSemanticValidator<ExecutionProfile> profileValidator)
    {
        ArgumentNullException.ThrowIfNull(specificationValidator);
        ArgumentNullException.ThrowIfNull(profileValidator);

        _specificationValidator = specificationValidator;
        _profileValidator = profileValidator;
    }

    /// <summary>Validates the selected exact references and the profile's dependency and policy closure.</summary>
    public ProgramKitValidationResult Validate(
        TestSpecification specification,
        ArtifactReference specificationReference,
        ExecutionProfile profile,
        ProfileReference profileReference,
        TestSpecificationSelection selection)
    {
        ArgumentNullException.ThrowIfNull(specification);
        ArgumentNullException.ThrowIfNull(specificationReference);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(profileReference);
        ArgumentNullException.ThrowIfNull(selection);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(_specificationValidator.Validate(specification).Diagnostics);
        diagnostics.AddRange(_profileValidator.Validate(profile).Diagnostics);

        QualityValidation.ValidateTestReference(
            specificationReference,
            "$.specificationReference",
            diagnostics);
        QualityValidation.ValidateProfileReference(
            profileReference,
            "$.profileReference",
            diagnostics);
        QualityValidation.ValidateTestReference(
            selection.Specification,
            "$.selection.specification",
            diagnostics);
        QualityValidation.ValidateProfileReference(
            selection.Profile,
            "$.selection.profile",
            diagnostics);
        if (selection.Specification != specificationReference)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt201,
                "The selected specification reference must match the validated specification exactly.",
                "$.selection.specification"));
        }

        if (selection.Profile != profileReference)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt202,
                "The selected profile reference must match the validated profile exactly.",
                "$.selection.profile"));
        }

        var requirements = specification.ExecutionRequirements;
        if (requirements is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (requirements.RunnerClasses.IsDefault
            || !requirements.RunnerClasses.Contains(profile.RunnerClass, StringComparer.Ordinal))
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt203,
                $"Runner class '{profile.RunnerClass}' is not permitted by the specification.",
                "$.profile.runnerClass"));
        }

        if (requirements.Platforms.IsDefault
            || !requirements.Platforms.Contains(profile.Platform, StringComparer.Ordinal))
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt204,
                $"Platform '{profile.Platform}' is not permitted by the specification.",
                "$.profile.platform"));
        }

        if (!requirements.RequiredDependencyClosure.IsDefault)
        {
            foreach (var dependency in requirements.RequiredDependencyClosure)
            {
                if (profile.DependencyClosure.IsDefault
                    || !profile.DependencyClosure.Contains(dependency))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt205,
                        $"The execution profile is missing required dependency '{dependency.Identity.Value}'.",
                        "$.profile.dependencyClosure"));
                }
            }
        }

        if (!requirements.EnvironmentAssumptions.IsDefault)
        {
            foreach (var assumption in requirements.EnvironmentAssumptions)
            {
                if (profile.EnvironmentAssumptions.IsDefault
                    || !profile.EnvironmentAssumptions.Contains(assumption, StringComparer.Ordinal))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt208,
                        $"The execution profile is missing required environment assumption '{assumption}'.",
                        "$.profile.environmentAssumptions"));
                }
            }
        }

        if (profile.Timeout > requirements.Timeout)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt206,
                "The execution profile timeout exceeds the specification limit.",
                "$.profile.timeout"));
        }

        if (profile.Retry is not null
            && requirements.Retry is not null
            && profile.Retry.MaximumAttempts > requirements.Retry.MaximumAttempts)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt207,
                "The execution profile retry count exceeds the specification limit.",
                "$.profile.retry.maximumAttempts"));
        }

        QualityValidation.ValidateAccessDoesNotExceed(
            requirements.Access,
            profile.Access,
            "$.profile.access",
            diagnostics);

        return ProgramKitValidationResult.From(diagnostics);
    }
}
