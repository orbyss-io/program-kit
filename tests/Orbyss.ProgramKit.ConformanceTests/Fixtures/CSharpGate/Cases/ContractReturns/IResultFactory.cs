namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ContractReturns;

internal interface IResultFactory
{
    OperationResult Create(bool succeeded);
}
