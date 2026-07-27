namespace ObservatoryScheduling.Tests.Operations.Migrations;

internal enum PendingWorkDisposition
{
    DrainObservedRevision,
    Coexist,
    Migrate,
    CancelAndRecreate,
    Block,
}
