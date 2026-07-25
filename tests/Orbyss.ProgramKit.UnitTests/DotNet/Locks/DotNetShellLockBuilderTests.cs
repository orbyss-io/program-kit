using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Configuration;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Serialization.Json.Contributions;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Locks;

[TestClass]
public sealed class DotNetShellLockBuilderTests
{
    [TestMethod]
    public void LockMaterializesEveryHostAndExactDotNet10PolicyDeterministically()
    {
        var shell = DotNetTestContractFactory.Shell();
        IDotNetShellValidator validator =
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator());
        DotNetShellLockBuilder sut = new(validator);
        var shellRevision = DotNetTestContractFactory.Ref("shell", "reviewed", '7');

        var first = sut.Build(shell, shellRevision);
        var second = sut.Build(shell, shellRevision);

        Assert.AreSequenceEqual(
            first.HostLocks.Select(static item =>
                string.Concat(
                    item.HostIdentity.Value,
                    "|",
                    item.PackageLockDigest.Value)),
            second.HostLocks.Select(static item =>
                string.Concat(
                    item.HostIdentity.Value,
                    "|",
                    item.PackageLockDigest.Value)));
        Assert.HasCount(3, first.HostLocks);
        Assert.IsTrue(first.HostLocks.All(static item =>
            item.Target.SdkVersion == "10.0.302" &&
            item.Target.TargetFramework == "net10.0" &&
            item.Target.LanguageVersion == "14.0" &&
            item.Target.RollForward == "disable" &&
            !item.Target.AllowPrerelease));
    }

    [TestMethod]
    public void SelectorRejectsKindMismatch()
    {
        var shell = DotNetTestContractFactory.Shell();
        IDotNetShellValidator validator =
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator());
        DotNetShellLockBuilder lockBuilder = new(validator);
        var document = lockBuilder.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        DotNetHostLockSelector sut = new();
        var console = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Console);

        var exception = Assert.ThrowsExactly<DotNetKitException>(() =>
            sut.Resolve(document, console.Identity, DotNetHostKind.Api));

        Assert.AreEqual(DotNetDiagnosticIds.InvalidHostSelection, exception.DiagnosticId);
    }

    [TestMethod]
    public void LockClosesOverConfigurationTasksSchedulesAndJsonContributions()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static item => item.Kind == DotNetHostKind.Api);
        var configuration = DotNetTestContractFactory.Ref(
            "schema",
            "api-configuration",
            '8');
        var runtime = DotNetTestContractFactory.Ref(
            "task-runtime",
            "in-process",
            '9');
        var scheduleProvider = DotNetTestContractFactory.Ref(
            "schedule-provider",
            "cron",
            'a');
        var contribution = new JsonSerializationContributionRef(
            DotNetTestContractFactory.Id("json-contribution", "api"),
            new SemanticVersion("1.0.0"),
            DotNetTestContractFactory.Digest('b'));
        api = api with
        {
            ConfigurationBindings =
            [
                api.ConfigurationBindings[0] with
                {
                    Definition = api.ConfigurationBindings[0].Definition with
                    {
                        SchemaRevision = configuration,
                    },
                },
            ],
            TaskRuntimeRequirements =
            [
                new DotNetTaskRuntimeRequirement(
                    runtime,
                    [scheduleProvider]),
            ],
        };
        shell = shell with
        {
            Hosts = shell.Hosts
                .Select(host => host.Kind == DotNetHostKind.Api ? api : host)
                .ToImmutableArray(),
            JsonSerialization = shell.JsonSerialization with
            {
                Contributions = [contribution],
            },
        };
        IDotNetShellValidator validator =
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator());
        DotNetShellLockBuilder sut = new(validator);

        var document = sut.Build(
            shell,
            DotNetTestContractFactory.Ref("shell", "reviewed", '7'));
        var hostLock = document.HostLocks.Single(static item =>
            item.Kind == DotNetHostKind.Api);

        Assert.Contains(configuration, hostLock.ContractRevisions);
        Assert.Contains(runtime, hostLock.ContractRevisions);
        Assert.Contains(scheduleProvider, hostLock.ContractRevisions);
        Assert.Contains(configuration, hostLock.SchemaRevisions);
        Assert.IsTrue(hostLock.SerializationRevisions.Any(reference =>
            reference.Identity == contribution.Identity &&
            reference.Version == contribution.Version &&
            reference.Digest == contribution.Digest));
    }
}
