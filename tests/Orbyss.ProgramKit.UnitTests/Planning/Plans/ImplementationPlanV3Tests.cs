using System.Collections.Immutable;
using Orbyss.ProgramKit.Planning.Plans;
using Orbyss.ProgramKit.Planning.Validation;

namespace Orbyss.ProgramKit.UnitTests.Planning.Plans;

[TestClass]
public sealed class ImplementationPlanV3Tests
{
    private static readonly ArtifactReference Matrix =
        Reference("pkid:activation-matrix:consumer:layered-build");
    private static readonly ArtifactReference Profile =
        Reference("pkid:profile:consumer:layered-build-full");

    [TestMethod]
    public void CreatePlansSupportSingleAndMultiUnitGateEstablishment()
    {
        var validator = CreateValidator();
        var single = CreatePlan(
            StaticConformancePlanState.CreateNew,
            [Unit("G1", PlanWorkUnitKind.GateEstablishment, [])],
            includeGateArtifacts: true);
        var multiple = CreatePlan(
            StaticConformancePlanState.CreateNew,
            [
                Unit("G1", PlanWorkUnitKind.GateEstablishment, []),
                Unit("G2", PlanWorkUnitKind.GateEstablishment, ["G1"]),
                Unit("P1", PlanWorkUnitKind.Product, ["G2"]),
                Unit("C1", PlanWorkUnitKind.Closure, ["P1"]),
            ],
            includeGateArtifacts: true);

        var singleResult = validator.Validate(single);
        var multipleResult = validator.Validate(multiple);

        Assert.IsTrue(singleResult.IsValid, Format(singleResult));
        Assert.IsTrue(multipleResult.IsValid, Format(multipleResult));
    }

    [TestMethod]
    public void DependencyRolesRejectProductBeforeGateAndClosureBeforeProduct()
    {
        var validator = CreateValidator();
        var productBeforeGate = CreatePlan(
            StaticConformancePlanState.CreateNew,
            [
                Unit("G1", PlanWorkUnitKind.GateEstablishment, []),
                Unit("P1", PlanWorkUnitKind.Product, []),
            ],
            includeGateArtifacts: true);
        var closureBeforeProduct = CreatePlan(
            StaticConformancePlanState.CreateNew,
            [
                Unit("G1", PlanWorkUnitKind.GateEstablishment, []),
                Unit("P1", PlanWorkUnitKind.Product, ["G1"]),
                Unit("C1", PlanWorkUnitKind.Closure, ["G1"]),
            ],
            includeGateArtifacts: true);

        var productResult = validator.Validate(productBeforeGate);
        var closureResult = validator.Validate(closureBeforeProduct);

        Assert.IsFalse(productResult.IsValid);
        Assert.IsFalse(closureResult.IsValid);
        Assert.IsTrue(productResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Message.Contains(
                "must depend explicitly or transitively on gate-establishment",
                StringComparison.Ordinal)));
        Assert.IsTrue(closureResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Message.Contains(
                "must depend explicitly or transitively on product",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void MissingProfileBlockedAndImplicitEmptyFailClosed()
    {
        var validator = CreateValidator();
        var missingProfile = CreatePlan(
            StaticConformancePlanState.ReuseExisting,
            [
                Unit("P1", PlanWorkUnitKind.Product, []) with
                {
                    VerificationProfile = null,
                },
            ],
            includeGateArtifacts: true,
            materializedGateArtifacts: true);
        var blocked = CreatePlan(
            StaticConformancePlanState.BlockedUnavailable,
            [Unit("P1", PlanWorkUnitKind.Product, [])],
            includeGateArtifacts: true);
        var implicitEmpty = CreatePlan(
            StaticConformancePlanState.AcceptedEmpty,
            [EmptyUnit("P1", PlanWorkUnitKind.Product, [])],
            includeGateArtifacts: false) with
        {
            StaticConformanceDisposition = null!,
        };
        var unsupportedDispositionVersion = CreatePlan(
            StaticConformancePlanState.AcceptedEmpty,
            [EmptyUnit("P1", PlanWorkUnitKind.Product, [])],
            includeGateArtifacts: false) with
        {
            StaticConformanceDisposition = Reference(
                "pkid:static-conformance-disposition:consumer:software") with
            {
                Version = new SemanticVersion("2.0.0"),
            },
        };

        Assert.IsFalse(validator.Validate(missingProfile).IsValid);
        Assert.IsFalse(validator.Validate(blocked).IsValid);
        Assert.IsFalse(validator.Validate(implicitEmpty).IsValid);
        Assert.IsFalse(
            validator.Validate(unsupportedDispositionVersion).IsValid);
    }

    [TestMethod]
    public void ExactAcceptedEmptyDispositionPermitsUngatedProductAndClosure()
    {
        var plan = CreatePlan(
            StaticConformancePlanState.AcceptedEmpty,
            [
                EmptyUnit("P1", PlanWorkUnitKind.Product, []),
                EmptyUnit("C1", PlanWorkUnitKind.Closure, ["P1"]),
            ],
            includeGateArtifacts: false);
        var validator = CreateValidator();
        ImplementationPlanV3AdmissionEvaluator evaluator = new(validator);

        var validation = validator.Validate(plan);
        var first = evaluator.Evaluate(plan, [], Disposition(plan), null);
        var closure = evaluator.Evaluate(
            plan,
            ["P1"],
            Disposition(plan),
            null);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.AreSequenceEqual(["P1"], first.AdmissibleWorkUnitIds);
        Assert.AreSequenceEqual(["C1"], closure.AdmissibleWorkUnitIds);
    }

    [TestMethod]
    public void CreateAdmissionAllowsOnlyEstablishmentUntilCompatibleActivation()
    {
        var plan = CreatePlan(
            StaticConformancePlanState.CreateNew,
            [
                Unit("G1", PlanWorkUnitKind.GateEstablishment, []),
                Unit("G2", PlanWorkUnitKind.GateEstablishment, ["G1"]),
                Unit("P1", PlanWorkUnitKind.Product, ["G2"]),
            ],
            includeGateArtifacts: true);
        var validator = CreateValidator();
        ImplementationPlanV3AdmissionEvaluator sut = new(validator);

        var first = sut.Evaluate(plan, [], Disposition(plan), null);
        var second = sut.Evaluate(
            plan,
            ["G1"],
            Disposition(plan),
            null);
        var product = sut.Evaluate(
            plan,
            ["G1", "G2"],
            Disposition(plan),
            Snapshot(plan));

        Assert.AreSequenceEqual(["G1"], first.AdmissibleWorkUnitIds);
        Assert.AreSequenceEqual(["G2"], second.AdmissibleWorkUnitIds);
        Assert.AreSequenceEqual(["P1"], product.AdmissibleWorkUnitIds);
    }

    [TestMethod]
    public void ReusePreflightRejectsStaleLockAndAcceptsExactSnapshot()
    {
        var plan = CreatePlan(
            StaticConformancePlanState.ReuseExisting,
            [Unit("P1", PlanWorkUnitKind.Product, [])],
            includeGateArtifacts: true,
            materializedGateArtifacts: true);
        var validator = CreateValidator();
        ImplementationPlanV3AdmissionEvaluator sut = new(validator);
        var compatible = Snapshot(plan);
        var stale = compatible with
        {
            SelectionLock = compatible.SelectionLock with
            {
                Digest = new Sha256Digest(
                    "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
            },
        };

        var staleResult = sut.Evaluate(
            plan,
            [],
            Disposition(plan),
            stale);
        var compatibleResult = sut.Evaluate(
            plan,
            [],
            Disposition(plan),
            compatible);

        Assert.IsEmpty(staleResult.AdmissibleWorkUnitIds);
        Assert.IsNotEmpty(staleResult.BlockingReasons);
        Assert.AreSequenceEqual(
            ["P1"],
            compatibleResult.AdmissibleWorkUnitIds);
    }

    [TestMethod]
    public void AdmissionRejectsMissingStaleOrRelabeledDisposition()
    {
        var plan = CreatePlan(
            StaticConformancePlanState.AcceptedEmpty,
            [EmptyUnit("P1", PlanWorkUnitKind.Product, [])],
            includeGateArtifacts: false);
        ImplementationPlanV3AdmissionEvaluator sut =
            new(CreateValidator());
        var exact = Disposition(plan);
        var stale = exact with
        {
            Disposition = exact.Disposition with
            {
                Digest = new Sha256Digest(
                    "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
            },
        };
        var relabeled = exact with
        {
            State = StaticConformancePlanState.ReuseExisting,
        };

        var missingResult = sut.Evaluate(plan, [], null, null);
        var staleResult = sut.Evaluate(plan, [], stale, null);
        var relabeledResult = sut.Evaluate(plan, [], relabeled, null);
        var exactResult = sut.Evaluate(plan, [], exact, null);

        Assert.IsEmpty(missingResult.AdmissibleWorkUnitIds);
        Assert.IsEmpty(staleResult.AdmissibleWorkUnitIds);
        Assert.IsEmpty(relabeledResult.AdmissibleWorkUnitIds);
        Assert.AreSequenceEqual(["P1"], exactResult.AdmissibleWorkUnitIds);
    }

    [TestMethod]
    public void V2ToV3MigrationRequiresEveryExplicitWorkUnitBinding()
    {
        var source = VersionTwoPlan(
        [
            VersionTwoUnit("G1", []),
            VersionTwoUnit("P1", ["G1"]),
        ]);
        var supplied = new ImplementationPlanV3MigrationInput(
            Reference(
                "pkid:static-conformance-disposition:consumer:software"),
            StaticConformancePlanState.CreateNew,
            Reference("pkid:design:consumer:layered-build-gate"),
            Planned("pkid:gate-definition:consumer:layered-build", false),
            Planned("pkid:selection-lock:consumer:layered-build", false),
            Planned("pkid:evidence:consumer:layered-build-activation", false),
            [
                new PlanWorkUnitV3Binding(
                    "G1",
                    PlanWorkUnitKind.GateEstablishment,
                    Matrix,
                    Profile),
                new PlanWorkUnitV3Binding(
                    "P1",
                    PlanWorkUnitKind.Product,
                    Matrix,
                    Profile),
            ]);

        var first = ImplementationPlanV2ToV3Migration.Migrate(source, supplied);
        var second = ImplementationPlanV2ToV3Migration.Migrate(source, supplied);
        var incomplete = supplied with
        {
            WorkUnitBindings = [supplied.WorkUnitBindings[0]],
        };

        Assert.AreEqual(
            first.StaticConformanceDisposition,
            second.StaticConformanceDisposition);
        Assert.AreEqual(
            first.StaticConformanceState,
            second.StaticConformanceState);
        Assert.AreSequenceEqual(first.WorkUnits, second.WorkUnits);
        Assert.AreEqual("G1", source.WorkUnits[0].WorkUnitId);
        Assert.ThrowsExactly<ArgumentException>(() =>
            ImplementationPlanV2ToV3Migration.Migrate(source, incomplete));
    }

    [TestMethod]
    public void ExactV3MigrationFixtureConformsToRegisteredSchema()
    {
        var root = FindProgramKitRoot();
        var bytes = File.ReadAllBytes(Path.Combine(
            root.FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "migrations",
            "fixtures",
            "implementation-plan-v3-gate-establishment.json"));
        PlanCompositeSchemaModule schemas = new(
        [
            new ArtifactsSchemaModule(),
            new QualitySchemaModule(),
            new PlanningSchemaModule(),
        ]);
        var schema = schemas.Resources.Single(resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:implementation-plan" &&
            resource.SchemaReference.Version.Value == "3.0.0");
        JsonSchemaWorkbenchValidator sut = new(
            new ProgramKitJsonCanonicalizer(),
            new ProgramKitSchemaModuleValidator());

        var result = sut.Validate(
            bytes,
            schemas,
            schema.SchemaReference,
            new JsonSerializationLimits(
                MaxUtf8Bytes: 1_000_000,
                MaxDepth: 64,
                MaxTokens: 100_000,
                MaxObjectMembers: 100_000,
                MaxBufferedObjectBytes: 1_000_000));

        Assert.IsTrue(result.IsValid, Format(result));
    }

    private static ImplementationPlanDocumentV3Validator CreateValidator()
    {
        ImplementationPlanDocumentValidator versionTwo =
            new(new DefaultArtifactEnvelopeValidator());
        return new ImplementationPlanDocumentV3Validator(versionTwo);
    }

    private static ImplementationPlanDocumentV3 CreatePlan(
        StaticConformancePlanState state,
        ImmutableArray<PlanWorkUnitV3> units,
        bool includeGateArtifacts,
        bool materializedGateArtifacts = false)
    {
        var workUnitIds = units
            .Select(static unit => unit.WorkUnitId)
            .ToImmutableArray();
        return new ImplementationPlanDocumentV3(
            Reference("pkid:design:consumer:software"),
            new ProgramKitIdentifier("pkid:domain:consumer:software"),
            ImplementationPlanState.ReadyForHumanDecision,
            ["R1"],
            units,
            [],
            [
                new RequirementTrace(
                    "R1",
                    new ProgramKitIdentifier("pkid:domain:consumer:software"),
                    Reference("pkid:contract:consumer:software"),
                    workUnitIds,
                    "Implement the approved software.",
                    [],
                    [],
                    [],
                    "The software is implemented."),
            ],
            [],
            Reference(
                "pkid:static-conformance-disposition:consumer:software"),
            state,
            includeGateArtifacts
                ? Reference("pkid:design:consumer:layered-build-gate")
                : null,
            includeGateArtifacts
                ? Planned(
                    "pkid:gate-definition:consumer:layered-build",
                    materializedGateArtifacts)
                : null,
            includeGateArtifacts
                ? Planned(
                    "pkid:selection-lock:consumer:layered-build",
                    materializedGateArtifacts)
                : null,
            includeGateArtifacts
                ? Planned(
                    "pkid:evidence:consumer:layered-build-activation",
                    materializedGateArtifacts)
                : null);
    }

    private static PlanWorkUnitV3 Unit(
        string id,
        PlanWorkUnitKind kind,
        ImmutableArray<string> dependsOn) =>
        VersionThreeUnit(id, kind, dependsOn, Matrix, Profile);

    private static PlanWorkUnitV3 EmptyUnit(
        string id,
        PlanWorkUnitKind kind,
        ImmutableArray<string> dependsOn) =>
        VersionThreeUnit(id, kind, dependsOn, null, null);

    private static PlanWorkUnitV3 VersionThreeUnit(
        string id,
        PlanWorkUnitKind kind,
        ImmutableArray<string> dependsOn,
        ArtifactReference? matrix,
        ArtifactReference? profile)
    {
        var versionTwo = VersionTwoUnit(id, dependsOn);
        var result = new PlanWorkUnitV3(
            versionTwo.WorkUnitId,
            versionTwo.RequiredOutcome,
            versionTwo.Sequence,
            versionTwo.ParallelGroupId,
            versionTwo.DependsOn,
            versionTwo.Inputs,
            versionTwo.Outputs,
            versionTwo.AllowedEdits,
            versionTwo.SourceDependencies,
            versionTwo.ExternalDependencies,
            versionTwo.Migrations,
            versionTwo.Compatibility,
            versionTwo.StopConditions,
            versionTwo.Verification,
            versionTwo.SelectedTests,
            kind,
            matrix,
            profile);
        return kind == PlanWorkUnitKind.GateEstablishment
            ? result with
            {
                Inputs =
                [
                    Reference("pkid:design:consumer:software"),
                    Reference("pkid:design:consumer:layered-build-gate"),
                ],
                Outputs =
                [
                    Planned(
                        "pkid:gate-definition:consumer:layered-build",
                        false),
                    Planned(
                        "pkid:selection-lock:consumer:layered-build",
                        false),
                    Planned(
                        "pkid:evidence:consumer:layered-build-activation",
                        false),
                ],
            }
            : result;
    }

    private static PlanWorkUnit VersionTwoUnit(
        string id,
        ImmutableArray<string> dependsOn) =>
        new(
            id,
            $"Implement {id}.",
            id[0] switch
            {
                'G' => (id[1] - '0') * 10,
                'P' => 100 + (id[1] - '0'),
                'C' => 200 + (id[1] - '0'),
                _ => throw new ArgumentOutOfRangeException(nameof(id)),
            },
            null,
            dependsOn,
            [Reference("pkid:design:consumer:software")],
            [Planned($"pkid:plan-output:consumer:{id.ToLowerInvariant()}", false)],
            ["src/"],
            [],
            [],
            [],
            [],
            ["Stop on deviation."],
            [
                new PlanVerificationCommand(
                    "dotnet",
                    ["test"],
                    ".",
                    "All selected verification passes."),
            ],
            []);

    private static ImplementationPlanDocument VersionTwoPlan(
        ImmutableArray<PlanWorkUnit> units) =>
        new(
            Reference("pkid:design:consumer:software"),
            new ProgramKitIdentifier("pkid:domain:consumer:software"),
            ImplementationPlanState.ReadyForHumanDecision,
            ["R1"],
            units,
            [],
            [
                new RequirementTrace(
                    "R1",
                    new ProgramKitIdentifier("pkid:domain:consumer:software"),
                    Reference("pkid:contract:consumer:software"),
                    units.Select(static unit => unit.WorkUnitId)
                        .ToImmutableArray(),
                    "Implement the approved software.",
                    [],
                    [],
                    [],
                    "The software is implemented."),
            ],
            []);

    private static StaticConformanceExecutionSnapshot Snapshot(
        ImplementationPlanDocumentV3 plan) =>
        new(
            Materialize(plan.SelectionLock!),
            Materialize(plan.ActivationEvidence!),
            [Matrix],
            [Profile]);

    private static StaticConformanceDispositionSnapshot Disposition(
        ImplementationPlanDocumentV3 plan) =>
        new(plan.StaticConformanceDisposition, plan.StaticConformanceState);

    private static ArtifactReference Materialize(
        PlannedArtifactReference value) =>
        new(
            value.Identity,
            value.Version,
            value.IntegrityDigest ??
            new Sha256Digest(
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"));

    private static PlannedArtifactReference Planned(
        string identity,
        bool materialized) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            materialized
                ? PlannedArtifactState.Materialized
                : PlannedArtifactState.Prospective,
            materialized
                ? new Sha256Digest(
                    "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
                : null);

    private static ArtifactReference Reference(string identity) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));

    private static DirectoryInfo FindProgramKitRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException("Program Kit root was not found.");
    }
}
