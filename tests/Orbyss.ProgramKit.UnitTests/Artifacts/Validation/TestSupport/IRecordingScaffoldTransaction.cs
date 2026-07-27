using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation.TestSupport;

internal interface IRecordingScaffoldTransaction :
    IConsumerAnalyzerScaffoldTransaction
{
    bool Committed { get; }

    bool RolledBack { get; }
}
