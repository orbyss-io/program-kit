using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.OpenConsole.Contracts.Validation;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation;

[TestClass]
public sealed class OpenConsoleAlpha2ContractTests
{
    [TestMethod]
    public void CheckedInAlpha2RequestCarriesAValidExactConsoleProjection()
    {
        var document = ReadDocument();
        var result = CreateValidator().Validate(document);

        Assert.IsTrue(
            result.IsValid,
            string.Join(
                Environment.NewLine,
                result.Diagnostics.Select(static diagnostic =>
                    string.Concat(
                        diagnostic.Path,
                        " ",
                        diagnostic.Message))));
    }

    [TestMethod]
    public void HostRoleZeroAndCollisionFailAtTheirExactBoundary()
    {
        var document = ReadDocument();
        var zero = document with
        {
            HostExitCodeRoles = new OpenConsoleHostExitCodeRoles(0, 1, 3),
        };
        var collision = document with
        {
            HostExitCodeRoles = new OpenConsoleHostExitCodeRoles(2, 2, 3),
        };

        AssertPath(CreateValidator().Validate(zero), "/hostExitCodeRoles");
        AssertPath(CreateValidator().Validate(collision), "/hostExitCodeRoles");
    }

    [TestMethod]
    public void IncompleteAndDuplicateExitMapsFailAtTheCommandExitMap()
    {
        var document = ReadDocument();
        var command = document.Commands[0];
        var incomplete = ReplaceFirst(
            document,
            command with
            {
                ExitCodes = command.ExitCodes.RemoveAt(
                    command.ExitCodes.Length - 1),
            });
        var duplicate = ReplaceFirst(
            document,
            command with
            {
                ExitCodes = command.ExitCodes.Add(command.ExitCodes[0]),
            });

        AssertPath(
            CreateValidator().Validate(incomplete),
            "/commands/0/exitCodes");
        AssertPath(
            CreateValidator().Validate(duplicate),
            "/commands/0/exitCodes");
    }

    [TestMethod]
    public void PresentStreamWithoutARevisionFailsAtThatStream()
    {
        var document = ReadDocument();
        var command = document.Commands[0];
        var invalid = ReplaceFirst(
            document,
            command with
            {
                StandardOutput = new OpenConsoleStreamContract(
                    "stdout",
                    "application/json",
                    null!,
                    true),
            });

        AssertPath(
            CreateValidator().Validate(invalid),
            "/commands/0/standardOutput/schemaRevision");
    }

    [TestMethod]
    public void RequestResultAndDiagnosticSetSupersetsAndSubsetsFail()
    {
        var request = ReadRequest();
        var document = ToDocument(request);
        var command = document.Commands[0];
        var extra = document.Commands[1].OperationRevision;
        var invalidDocuments = new[]
        {
            ReplaceFirst(
                document,
                command with
                {
                    RequestSchemaRevisions =
                        command.RequestSchemaRevisions.Add(extra),
                }),
            ReplaceFirst(
                document,
                command with
                {
                    RequestSchemaRevisions = [],
                }),
            ReplaceFirst(
                document,
                command with
                {
                    ResultSchemaRevisions =
                        command.ResultSchemaRevisions.Add(extra),
                }),
            ReplaceFirst(
                document,
                command with
                {
                    ResultSchemaRevisions = [],
                }),
            ReplaceFirst(
                document,
                command with
                {
                    DiagnosticSchemaRevisions =
                        command.DiagnosticSchemaRevisions.Add(extra),
                }),
            ReplaceFirst(
                document,
                command with
                {
                    DiagnosticSchemaRevisions = [],
                }),
        };
        var host = request.Shell.Hosts.Single(candidate =>
            candidate.Identity == request.HostIdentity &&
            candidate.Kind == DotNetHostKind.Console);

        foreach (var invalid in invalidDocuments)
        {
            Assert.IsFalse(
                DotNetConsoleProjectionValidator.IsExactAlpha2(
                    host,
                    invalid.Commands));
        }
    }

    private static OpenConsoleDocumentAlpha2 ReadDocument() =>
        ToDocument(ReadRequest());

    private static DotNetConsoleInputMaterializationRequestAlpha2 ReadRequest()
    {
        return CreateSerializer().Read<
            DotNetConsoleInputMaterializationRequestAlpha2>(
                File.ReadAllBytes(Path.Combine(
                    FindProgramKitRoot(),
                    "tests",
                    "Fixtures",
                    "ConsumerCliConsole",
                    "console-input-request-alpha2.json")),
                DotNetJsonProfiles.ShellBootstrap.Reference,
                JsonSerializationLimits.Default);
    }

    private static OpenConsoleDocumentAlpha2 ToDocument(
        DotNetConsoleInputMaterializationRequestAlpha2 request) =>
        new(
            request.OpenConsole.Schema,
            request.OpenConsole.DocumentVersion,
            request.OpenConsole.Info,
            request.OpenConsole.HostRevision,
            request.OpenConsole.Parsing,
            request.OpenConsole.HostExitCodeRoles,
            request.OpenConsole.GlobalOptions,
            request.OpenConsole.Commands,
            request.OpenConsole.Help,
            request.OpenConsole.Completion,
            request.OpenConsole.Compatibility,
            new OpenConsoleProvenance(
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:shell:program-kit:alpha2-test"),
                    new SemanticVersion("0.1.0-alpha.1"),
                    new Sha256Digest(
                        "sha256:0000000000000000000000000000000000000000000000000000000000000000")),
                request.OpenConsole.GeneratorRevision,
                request.OpenConsole.OperationRevisions));

    private static OpenConsoleDocumentAlpha2 ReplaceFirst(
        OpenConsoleDocumentAlpha2 document,
        OpenConsoleCommandAlpha2 command) =>
        document with
        {
            Commands = document.Commands.SetItem(0, command),
        };

    private static OpenConsoleDocumentAlpha2Validator CreateValidator() =>
        new(new OpenConsoleDocumentValidator());

    private static void AssertPath(
        ProgramKitValidationResult result,
        string path)
    {
        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            string.Equals(diagnostic.Path, path, StringComparison.Ordinal)));
    }

    private static ProgramKitJsonSerializer CreateSerializer()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder builder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(builder);
        return new ProgramKitJsonSerializer(
            builder.Freeze(),
            new ProgramKitJsonCanonicalizer());
    }

    private static string FindProgramKitRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null &&
               !File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
        {
            current = current.Parent;
        }

        return current?.FullName ??
            throw new InvalidOperationException(
                "The Program Kit repository root was not found.");
    }
}
