namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ContractReturns;

internal sealed record OperationResult(bool Succeeded) : IOperationResult;
