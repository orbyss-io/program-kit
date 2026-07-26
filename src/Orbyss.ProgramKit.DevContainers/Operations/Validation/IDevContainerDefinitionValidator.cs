using Orbyss.ProgramKit.DevContainers.Contracts.Definitions;

namespace Orbyss.ProgramKit.DevContainers.Operations.Validation;

/// <summary>Validates one Dev Container definition without ambient state.</summary>
public interface IDevContainerDefinitionValidator :
    IProgramKitSemanticValidator<DevContainerDefinition>;
