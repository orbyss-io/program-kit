namespace Orbyss.ProgramKit.DotNet.Generation.Aspire;

/// <summary>Passes one declared parameter to one resource environment variable.</summary>
public sealed record AspireEnvironmentBinding(
    string ResourceName,
    string VariableName,
    string ParameterName);
