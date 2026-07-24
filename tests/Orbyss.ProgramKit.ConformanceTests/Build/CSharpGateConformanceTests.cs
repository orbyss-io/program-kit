using System.Diagnostics;
using System.Security.Cryptography;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
[TestCategory("ProgramKitGateExhaustive")]
[DoNotParallelize]
public sealed class CSharpGateConformanceTests
{
    private const int MatrixLaneCount = 4;

    private static readonly string[] ValidSourceCases =
    [
        "Valid",
        "InternalClass",
        "PublicStaticLogic",
        "ContractReturns",
        "ValidConstructorInjection",
        "ValidUnusedConstructorInjection",
        "ValidPrimaryConstructorInjection",
        "ValidPrimaryStructInjection",
        "ValidWrappedConstructorInjection",
        "ValidAsyncResultCarrier",
        "ValidConditionalConstructorInjection",
        "ValidEarlyReturnAfterInjection",
        "ValidDelegatingConstructorInjection",
        "ValidPrimaryConstructorDelegation",
        "ValidStaticHelperState",
        "GeneratedFrameworkContext",
        "ContractedGeneratedFrameworkContext",
    ];

    private static readonly (string Case, string Diagnostic)[] SourceCases =
    [
        ("MultipleTypes", "PKCS001"),
        ("FileName", "PKCS002"),
        ("Root", "PKCS003"),
        ("Namespace", "PKCS004"),
        ("ImmediateInvocation", "PKCS005"),
        ("ImmediateInvocationConditional", "PKCS005"),
        ("ImmediateInvocationConditionalAccess", "PKCS005"),
        ("ImmediateInvocationConversions", "PKCS005"),
        ("ImmediateInvocationDynamic", "PKCS005"),
        ("ImmediateInvocationExtension", "PKCS005"),
        ("ImmediateInvocationPropertyChain", "PKCS005"),
        ("ImmediateInvocationTuple", "PKCS005"),
        ("ImmediateInvocationSwitch", "PKCS005"),
        ("ImmediateInvocationArray", "PKCS005"),
        ("ImmediateInvocationArrayReceiver", "PKCS005"),
        ("ImmediateInvocationAnonymous", "PKCS005"),
        ("ImmediateInvocationDelegate", "PKCS005"),
        ("ImmediateInvocationUnary", "PKCS005"),
        ("ImmediateInvocationAwait", "PKCS005"),
        ("WarningSuppression", "PKCS006"),
        ("NullableDisable", "PKCS007"),
        ("InternalHelper", "PKCS008"),
        ("InternalHelperAccessibility", "PKCS008"),
        ("FileInternalHelper", "PKCS008"),
        ("StaticContractHelper", "PKCS008"),
        ("ServiceConstruction", "PKCS009"),
        ("TargetTypedServiceConstruction", "PKCS009"),
        ("ServiceContract", "PKCS012"),
        ("ServiceContractDisposable", "PKCS012"),
        ("CanonicalizerContract", "PKCS012"),
        ("PartialBehaviorContract", "PKCS012"),
        ("StaticOnlyBehaviorContract", "PKCS012"),
        ("InheritedBehaviorContract", "PKCS012"),
        ("TypeFreeSource", "PKCS015"),
        ("TopLevelWithType", "PKCS015"),
        ("ConcreteConstructorDependency", "PKCS016"),
        ("ConcretePropertyDependency", "PKCS016"),
        ("ConcreteFieldDependency", "PKCS016"),
        ("ConstrainedConcreteConstructorDependency", "PKCS016"),
        ("MutableInterfacePropertyDependency", "PKCS016"),
        ("UnprovenancedInterfacePropertyDependency", "PKCS016"),
        ("MutableInterfaceFieldDependency", "PKCS016"),
        ("UnprovenancedInterfaceFieldDependency", "PKCS016"),
        ("Composition", "PKCS016"),
        ("ConcreteBuilderReturn", "PKCS018"),
        ("ConcreteRegistryFactoryReturn", "PKCS018"),
        ("GenericConcreteRegistryReturn", "PKCS018"),
        ("WrappedConcreteBehavioralReturn", "PKCS018"),
        ("InterfacePropertyConcreteReturn", "PKCS018"),
        ("PhysicalProgramKitHeader", "PKCS017"),
        ("StandardGeneratedHeader", "PKCS017"),
        ("GeneratedCodeAttributeClaim", "PKCS017"),
        ("CompilerGeneratedAttributeClaim", "PKCS017"),
        ("UnhyphenatedGeneratedHeader", "PKCS017"),
        ("UncontractedFactory", "PKCS012"),
        ("UncontractedService", "PKCS012"),
        ("UncontractedAbstractService", "PKCS012"),
        ("BuilderConstruction", "PKCS009"),
        ("ConcreteRegistryDependency", "PKCS016"),
        ("BehavioralRecordReturn", "PKCS018"),
        ("BehavioralResultReturn", "PKCS018"),
        ("MutableResultReturn", "PKCS018"),
        ("InheritedConcreteReturn", "PKCS018"),
        ("InterfaceInitializerDependency", "PKCS016"),
        ("ComputedInterfacePropertyDependency", "PKCS016"),
        ("WrappedInterfaceInitializerDependency", "PKCS016"),
        ("PositionalRecordDependency", "PKCS016"),
        ("MultipleConstructorDependency", "PKCS016"),
        ("MutablePrimaryConstructorCapture", "PKCS016"),
        ("PrimaryStructCapture", "PKCS016"),
        ("StaticBehavioralFieldDependency", "PKCS016"),
        ("StaticBehavioralDefaultDependency", "PKCS016"),
        ("StaticNovelBehavioralDependency", "PKCS016"),
        ("NovelBehaviorPartialContract", "PKCS012"),
        ("NovelBehaviorConstruction", "PKCS009"),
        ("ConditionalConstructorDependency", "PKCS016"),
        ("EarlyReturnConstructorDependency", "PKCS016"),
        ("UnforwardedDelegatingConstructorDependency", "PKCS016"),
        ("DelegatingConstructorOverwriteDependency", "PKCS016"),
        ("ExceptionalConstructorDependency", "PKCS016"),
        ("PropertyOnlyBehavioralRecordReturn", "PKCS018"),
        ("AbstractRegistryReturn", "PKCS018"),
        ("LeakyFrameworkFactory", "PKCS012"),
        ("UncontractedGeneratedFrameworkContext", "PKCS012"),
    ];

    private static readonly (string Property, string Value, string Diagnostic)[]
        PolicyOverrides =
        [
            ("ProgramKitCSharpGateEnabled", "false", "PKCS101"),
            ("TreatWarningsAsErrors", "false", "PKCS102"),
            ("NoWarn", "CS0168", "PKCS103"),
            ("WarningsNotAsErrors", "CS0168", "PKCS104"),
            ("Nullable", "disable", "PKCS105"),
            ("AnalysisLevel", "none", "PKCS106"),
            ("EnforceCodeStyleInBuild", "false", "PKCS107"),
            ("CodeAnalysisTreatWarningsAsErrors", "false", "PKCS108"),
            ("MSBuildTreatWarningsAsErrors", "false", "PKCS109"),
            ("RestoreTreatWarningsAsErrors", "false", "PKCS110"),
            ("MSBuildWarningsAsMessages", "CS0168", "PKCS111"),
            ("EnableNETAnalyzers", "false", "PKCS112"),
            ("RunAnalyzersDuringBuild", "false", "PKCS113"),
            ("RunAnalyzers", "false", "PKCS114"),
            ("ProvideCommandLineArgs", "false", "PKCS161"),
            ("UseSharedCompilation", "true", "PKCS169"),
            ("UseHostCompilerIfAvailable", "true", "PKCS170"),
            (
                "TargetsTriggeredByCompilation",
                "PrepareForBuild",
                "PKCS171"),
            ("WarningLevel", "0", "PKCS115"),
            ("CodeAnalysisRuleSet", "Configurations\\DisableGate.ruleset", "PKCS116"),
            ("AnalysisMode", "None", "PKCS117"),
            ("AnalysisLevelStyle", "none", "PKCS117"),
            ("EffectiveAnalysisLevel", "0.0", "PKCS117"),
            ("SkipGlobalAnalyzerConfigForPackage", "true", "PKCS117"),
            ("EffectiveCodeAnalysisTreatWarningsAsErrors", "false", "PKCS117"),
            ("MicrosoftCodeAnalysisNetAnalyzersRulesVersion", "none", "PKCS117"),
            ("DisabledWarnings", "CS0168", "PKCS123"),
            ("ProgramKitGeneratedSourceRoot", "Generated", "PKCS126"),
            ("ProgramKitCSharpGateProjectPath", "invalid-gate.csproj", "PKCS127"),
            ("ProgramKitCSharpGateAssemblyPath", "invalid-gate.dll", "PKCS128"),
            ("ProgramKitWarningApprovalLedgerPath", "invalid-ledger.tsv", "PKCS129"),
            ("SkipCompilerExecution", "true", "PKCS130"),
            ("BuildDependsOn", "", "PKCS131"),
            ("CoreBuildDependsOn", "", "PKCS132"),
            ("CompileDependsOn", "", "PKCS133"),
            ("OptimizeImplicitlyTriggeredBuild", "true", "PKCS134"),
            ("Features", "run-nullable-analysis=never", "PKCS135"),
            ("CompilerResponseFile", "Configurations\\compiler.rsp", "PKCS145"),
            ("CscToolPath", "Configurations", "PKCS146"),
            ("CscToolExe", "fake-csc.exe", "PKCS147"),
            ("BuildProjectReferences", "false", "PKCS151"),
            ("ProgramKitGeneratedSourceProbeProject", "CSharpGateProbe.csproj", "PKCS155"),
            ("ProgramKitConformanceValidatedGateDigest", "invalid", "PKCS118"),
            ("_SkipAnalyzers", "true", "PKCS159"),
            (
                "ResolvedCodeAnalysisRuleSet",
                "Configurations\\DisableGate.ruleset",
                "PKCS160"),
        ];

    private static readonly (string Mutation, string Diagnostic)[] LocalMutations =
    [
        ("LocalGateDisabled", "PKCS101"),
        ("LocalNoWarn", "PKCS103"),
        ("LocalWarningsNotAsErrors", "PKCS104"),
        ("LocalMSBuildWarningsAsMessages", "PKCS111"),
        ("LocalRunAnalyzersDisabled", "PKCS114"),
        ("LocalWarningLevelDisabled", "PKCS115"),
        ("LocalRuleSet", "PKCS116"),
        ("LocalAnalysisMode", "PKCS117"),
        ("LocalDisabledWarnings", "PKCS123"),
        ("RemoveAnalyzerProjectReference", "PKCS118"),
        ("DuplicateAnalyzerProjectReference", "PKCS118"),
        ("BuildReferenceFalse", "PKCS118"),
        ("TargetsGetTargetPath", "PKCS118"),
        ("SkipGetTargetFrameworkProperties", "PKCS118"),
        ("ProjectReferenceAdditionalProperties", "PKCS118"),
        ("ProjectReferenceGlobalPropertiesToRemove", "PKCS118"),
        ("RemoveProjectDirectoryCompilerProperty", "PKCS119"),
        ("RemoveProjectNameCompilerProperty", "PKCS119"),
        ("RemoveGeneratedSourceRootCompilerProperty", "PKCS119"),
        ("RemoveWarningApprovalLedgerPathCompilerProperty", "PKCS119"),
        ("RemoveRootNamespaceCompilerProperty", "PKCS119"),
        ("AnalyzerConfig", "PKCS120"),
        ("AnalyzerConfigInIntermediate", "PKCS120"),
        ("AnalyzerConfigInSdk", "PKCS120"),
        ("DetachResolvedAnalyzer", "PKCS121"),
        ("DuplicateResolvedAnalyzer", "PKCS121"),
        ("RemoveApprovalLedger", "PKCS122"),
        ("AddSecondApprovalLedger", "PKCS122"),
        ("RemoveSdkAnalyzer", "PKCS141"),
        ("CompilerResponseFileItem", "PKCS145"),
        ("InjectedAnalyzer", "PKCS148"),
        ("ConsumerSelfValidationAnalyzer", "PKCS148"),
        ("PostValidationRemoveAnalyzer", "PKCS168"),
        ("PostValidationRemoveSource", "PKCS163"),
        ("PostValidationWarningDemotion", "PKCS165"),
        ("PostValidationSkipCompilerExecution", "PKCS167"),
        ("PostValidationCompilerResponseFile", "PKCS167"),
        ("PostValidationCscToolSubstitution", "PKCS167"),
        ("PostValidationSkipAnalyzers", "PKCS167"),
        ("PostValidationDisableGeneratedReceipt", "PKCS167"),
        ("PostValidationEnableSharedCompilation", "PKCS167"),
        ("PostValidationEnableHostCompiler", "PKCS167"),
        ("PostValidationTargetFramework", "PKCS167"),
        ("PostValidationCompilationHook", "PKCS167"),
        ("PostValidationRemoveReference", "PKCS173"),
        ("PostValidationDesignTimeBecomesProducing", "PKCS167"),
        ("PostValidationDesignTimeControlMutation", "PKCS167"),
        ("ResolvedFrameworkIdentityMutation", "PKNET009"),
        ("ResolvedFrameworkVersionMutation", "PKNET010"),
        ("RawAssemblyReference", "PKCS176"),
        ("AliasedAssemblyReference", "PKCS176"),
        ("LinkedInteropReference", "PKCS176"),
        ("ComReference", "PKCS176"),
        ("AddedCompilerModule", "PKCS176"),
    ];

    private static readonly (string Case, string Diagnostic)[] InvalidLedgerCases =
    [
        ("AliasUnapproved", "PKCS006"),
        ("MalformedLedger", "PKCS013"),
        ("DuplicateLedger", "PKCS013"),
        ("StaleLedger", "PKCS013"),
    ];

    private static readonly (string Property, string Value, string Diagnostic)[]
        RestorePolicyOverrides =
        [
            ("TreatWarningsAsErrors", "false", "PKCS102"),
            ("WarningsNotAsErrors", "NU1903", "PKCS104"),
            ("MSBuildWarningsAsMessages", "NU1903", "PKCS111"),
            ("RestoreNoWarn", "NU1903", "PKCS124"),
            ("NuGetAudit", "false", "PKCS136"),
            ("NuGetAuditMode", "direct", "PKCS137"),
            ("NuGetAuditLevel", "high", "PKCS138"),
            ("RestoreIgnoreFailedSources", "true", "PKCS139"),
        ];

    [ClassInitialize]
    public static async Task PrepareValidatedGateConfigurations(TestContext _)
    {
        var restore = await RestoreProjectAsync(GetProbeProjectPath());
        Assert.AreEqual(0, restore.ExitCode, restore.Output);

        foreach (var configuration in GateConfigurations())
        {
            var gateBuild = await BuildProjectAsync(
                GetGateProjectPath(),
                configuration,
                ["--no-restore"]);
            Assert.AreEqual(0, gateBuild.ExitCode, gateBuild.Output);

            var gateAssembly = GetGateAssemblyPath(configuration);
            Assert.IsTrue(File.Exists(gateAssembly), gateAssembly);
            using var stream = File.OpenRead(gateAssembly);
            var digest = Convert.ToHexString(SHA256.HashData(stream));
            var receipt = GetValidatedGateReceiptPath(configuration);
            Directory.CreateDirectory(Path.GetDirectoryName(receipt)!);
            File.WriteAllText(receipt, digest);
        }
    }

    [TestMethod]
    public async Task ValidIntentGroupedSourcePassesTheGate()
    {
        var results = await RunBuildMatrixAsync(
            ValidSourceCases,
            static (gateCase, configuration) =>
                BuildProbeAsync(gateCase, configuration));

        for (var index = 0; index < ValidSourceCases.Length; index++)
        {
            var gateCase = ValidSourceCases[index];
            var result = results[index];

            Assert.AreEqual(
                0,
                result.ExitCode,
                $"{gateCase} unexpectedly failed.{Environment.NewLine}{result.Output}");
        }
    }

    [TestMethod]
    public async Task DefaultConfigurationResolvesTheGateAnalyzerPath()
    {
        var result = await RunDotNetProjectCommandAsync(
            "build",
            GetProbeProjectPath(),
            "--nologo",
            "--property:GateCase=Valid");

        Assert.AreEqual(0, result.ExitCode, result.Output);
    }

    [TestMethod]
    public async Task DotNetFormatCanLoadTheGatedWorkspace()
    {
        var debugGate = await RunDotNetProjectCommandAsync(
            "build",
            GetGateProjectPath(),
            "--configuration",
            "Debug",
            "--no-restore",
            "--no-incremental",
            "--nologo");
        Assert.AreEqual(0, debugGate.ExitCode, debugGate.Output);

        foreach (var workspace in new[]
                 {
                     GetProbeProjectPath(),
                     GetUnitTestProjectPath(),
                     GetSolutionPath(),
                 })
        {
            var result = await RunDotNetProjectCommandAsync(
                "format",
                workspace,
                "--no-restore",
                "--verify-no-changes",
                "--verbosity",
                "minimal");

            Assert.AreEqual(0, result.ExitCode, result.Output);
            Assert.DoesNotContain("Msbuild failed", result.Output);
        }
    }

    [TestMethod]
    public async Task GateImplementationPassesItsOwnAnalyzer()
    {
        var project = GetGateProjectPath();
        var result = await BuildProjectAsync(
            project,
            "--no-restore",
            "--no-incremental");

        Assert.AreEqual(0, result.ExitCode, result.Output);
    }

    [TestMethod]
    public async Task NormalGateBuildRunsMandatorySelfValidation()
    {
        var project = GetGateProjectPath();
        var result = await BuildProjectAsync(
            project,
            "--no-restore");

        Assert.AreEqual(0, result.ExitCode, result.Output);
        Assert.Contains(
            "Running mandatory Program Kit C# gate self-validation.",
            result.Output);
    }

    [TestMethod]
    public async Task ConcurrentCompilerInvocationsEmitDistinctNonceReceipts()
    {
        var temporaryDirectory = Directory.CreateTempSubdirectory(
            "program-kit-compiler-concurrency-");
        try
        {
            var firstProject = CreateExternalGeneratedProject(
                temporaryDirectory,
                "first");
            var secondProject = CreateExternalGeneratedProject(
                temporaryDirectory,
                "second");
            var programKitRoot = Path.Combine(
                ConformanceInputs.RepositoryRoot,
                "program-kit");
            var generatedSourceProject = Path.Combine(
                ConformanceInputs.RepositoryRoot,
                "program-kit",
                "tests",
                "Orbyss.ProgramKit.ConformanceTests",
                "Fixtures",
                "CSharpGate",
                "GeneratedSource",
                "Generator",
                "GeneratedSourceProbe.csproj");
            foreach (var project in new[] { firstProject, secondProject })
            {
                var restore = await RestoreProjectAsync(
                    project,
                    $"--property:ProgramKitBuildRoot={programKitRoot}",
                    "--property:GeneratedGateCase=Valid",
                    $"--property:ProgramKitGeneratedSourceProbeProject={generatedSourceProject}");
                Assert.AreEqual(0, restore.ExitCode, restore.Output);
            }

            var orchestrationProject = Path.Combine(
                temporaryDirectory.FullName,
                "ConcurrentBuild.proj");
            File.WriteAllLines(
                orchestrationProject,
                [
                    "<Project>",
                    "  <ItemGroup>",
                    "    <ConcurrentProject Include=\"first\\GeneratedHost.csproj\" />",
                    "    <ConcurrentProject Include=\"second\\GeneratedHost.csproj\" />",
                    "  </ItemGroup>",
                    "  <Target Name=\"Build\">",
                    "    <MSBuild Projects=\"@(ConcurrentProject)\"",
                    "             Targets=\"Build\"",
                    "             BuildInParallel=\"true\"",
                    "             Properties=\"Configuration=$(Configuration);" +
                    "ProgramKitBuildRoot=$(ProgramKitBuildRoot);" +
                    "GeneratedGateCase=Valid;" +
                    "ProgramKitGeneratedSourceProbeProject=" +
                    "$(ProgramKitGeneratedSourceProbeProject)\" />",
                    "  </Target>",
                    "</Project>",
                ]);
            var build = await RunDotNetProjectCommandAsync(
                "msbuild",
                orchestrationProject,
                "--nologo",
                "--maxcpucount",
                "--target:Build",
                "--property:Configuration=Release",
                $"--property:ProgramKitBuildRoot={programKitRoot}",
                $"--property:ProgramKitGeneratedSourceProbeProject={generatedSourceProject}");
            Assert.AreEqual(0, build.ExitCode, build.Output);

            var nonces = new HashSet<string>(StringComparer.Ordinal);
            foreach (var project in new[] { firstProject, secondProject })
            {
                var receiptRoot = Path.Combine(
                    Path.GetDirectoryName(project)!,
                    "obj",
                    "ProgramKitCompilerGenerated",
                    "net10.0");
                var receipts = Directory.GetFiles(
                    receiptRoot,
                    "ProgramKitCompilerInvocationReceipt.*.cs",
                    SearchOption.AllDirectories);
                Assert.HasCount(1, receipts);
                AssertCompilerInvocationReceipt(receipts[0], nonces);
            }
            Assert.HasCount(2, nonces);
        }
        finally
        {
            DeleteTemporaryDirectory(temporaryDirectory);
        }
    }

    [TestMethod]
    public async Task GateSelfValidationActuallyExecutesTheAnalyzer()
    {
        var project = GetGateProjectPath();
        var result = await BuildProjectAsync(
            project,
            "--no-restore",
            "--property:RootNamespace=Invalid.Root");

        Assert.AreNotEqual(0, result.ExitCode, result.Output);
        Assert.Contains("PKCS004", result.Output);
    }

    [TestMethod]
    public async Task GateSelfValidationCannotBeSpoofedByACommandLineCaller()
    {
        var project = GetGateProjectPath();
        var analyzer = Path.Combine(
            Path.GetDirectoryName(project)!,
            "bin",
            "Release",
            "net10.0",
            "Orbyss.ProgramKit.CSharpGate.dll");
        var result = await BuildProjectAsync(
            project,
            "--no-restore",
            "--property:ProgramKitSelfValidate=true",
            $"--property:ProgramKitSelfValidationAnalyzerPath={analyzer}");

        Assert.AreNotEqual(0, result.ExitCode, result.Output);
        Assert.Contains("PKCS149", result.Output);
    }

    [TestMethod]
    public async Task EverySourceRuleFailsWithItsStableDiagnostic()
    {
        var results = await RunBuildMatrixAsync(
            SourceCases,
            static (sourceCase, configuration) =>
                BuildProbeAsync(sourceCase.Case, configuration));

        for (var index = 0; index < SourceCases.Length; index++)
        {
            var (gateCase, diagnostic) = SourceCases[index];
            var result = results[index];

            Assert.AreNotEqual(
                0,
                result.ExitCode,
                $"{gateCase} unexpectedly passed.{Environment.NewLine}{result.Output}");
            Assert.Contains(diagnostic, result.Output);
        }
    }

    [TestMethod]
    public async Task EveryWarningPolicyOverrideFailsClosed()
    {
        var results = await RunBuildMatrixAsync(
            PolicyOverrides,
            static (policyOverride, configuration) =>
                BuildProbeAsync(
                    "Valid",
                    configuration,
                    policyOverride.Property,
                    policyOverride.Value,
                    reuseValidatedGate:
                        policyOverride.Property ==
                        "ProgramKitConformanceValidatedGateDigest"));

        for (var index = 0; index < PolicyOverrides.Length; index++)
        {
            var (property, _, diagnostic) = PolicyOverrides[index];
            var result = results[index];

            Assert.AreNotEqual(
                0,
                result.ExitCode,
                $"{property} unexpectedly passed.{Environment.NewLine}{result.Output}");
            Assert.Contains(diagnostic, result.Output);
        }
    }

    [TestMethod]
    public async Task ProjectLocalOverridesAndAnalyzerDetachmentFailClosed()
    {
        var results = await RunBuildMatrixAsync(
            LocalMutations,
            static (mutation, configuration) =>
                BuildProbeMutationAsync(mutation.Mutation, configuration));

        for (var index = 0; index < LocalMutations.Length; index++)
        {
            var (mutation, diagnostic) = LocalMutations[index];
            var result = results[index];

            Assert.AreNotEqual(
                0,
                result.ExitCode,
                $"{mutation} unexpectedly passed.{Environment.NewLine}{result.Output}");
            Assert.Contains(diagnostic, result.Output);
        }
    }

    [TestMethod]
    public async Task SamePathCompilerInputMutationFailsClosed()
    {
        var project = GetProbeProjectPath();
        var control = await BuildProjectAsync(
            project,
            "--no-restore",
            "--no-incremental",
            "--property:GateCase=Valid");
        Assert.AreEqual(0, control.ExitCode, control.Output);

        var editorConfig = Path.Combine(
            Path.GetDirectoryName(project)!,
            "obj",
            "Release",
            "net10.0",
            "CSharpGateProbe.GeneratedMSBuildEditorConfig.editorconfig");
        Assert.IsTrue(File.Exists(editorConfig), editorConfig);
        var originalContent = File.ReadAllBytes(editorConfig);
        try
        {
            var result = await BuildProjectAsync(
                project,
                "--no-restore",
                "--no-incremental",
                "--property:GateCase=Valid",
                "--property:GateMutation=PostValidationMutateAnalyzerConfig");

            Assert.AreNotEqual(0, result.ExitCode, result.Output);
            Assert.Contains("PKCS175", result.Output);
        }
        finally
        {
            File.WriteAllBytes(editorConfig, originalContent);
        }
    }

    [TestMethod]
    public async Task RestoreWarningSuppressionFailsDuringRestore()
    {
        var project = GetProbeProjectPath();
        foreach (var (property, value, diagnostic) in RestorePolicyOverrides)
        {
            var result = await RestoreProjectAsync(
                project,
                $"--property:{property}={value}");

            Assert.AreNotEqual(0, result.ExitCode, result.Output);
            Assert.Contains(diagnostic, result.Output);
        }

        var suppressedAudit = await RestoreProjectAsync(
            project,
            "--property:GateMutation=RestoreAuditSuppress");
        Assert.AreNotEqual(0, suppressedAudit.ExitCode, suppressedAudit.Output);
        Assert.Contains("PKCS140", suppressedAudit.Output);

        var packageReferenceSuppression = await RestoreProjectAsync(
            project,
            "--property:GateMutation=PackageReferenceNoWarn");
        Assert.AreNotEqual(
            0,
            packageReferenceSuppression.ExitCode,
            packageReferenceSuppression.Output);
        Assert.Contains("PKCS143", packageReferenceSuppression.Output);

        var projectReferenceSuppression = await RestoreProjectAsync(
            project,
            "--property:GateMutation=ProjectReferenceNoWarn");
        Assert.AreNotEqual(
            0,
            projectReferenceSuppression.ExitCode,
            projectReferenceSuppression.Output);
        Assert.Contains("PKCS144", projectReferenceSuppression.Output);
    }

    [TestMethod]
    public async Task ExplicitGateImportsAnalyzeExternalGeneratedSources()
    {
        var valid = await BuildExternalGeneratedProjectAsync("Valid");
        Assert.AreEqual(0, valid.ExitCode, valid.Output);

        var generatedAncestor = await BuildExternalGeneratedProjectAsync(
            "Valid",
            useGeneratedAncestor: true);
        Assert.AreEqual(0, generatedAncestor.ExitCode, generatedAncestor.Output);

        var invalid = await BuildExternalGeneratedProjectAsync("Invalid");
        Assert.AreNotEqual(0, invalid.ExitCode, invalid.Output);
        Assert.Contains("PKCS001", invalid.Output);

        var wrongHint = await BuildExternalGeneratedProjectAsync("WrongHint");
        Assert.AreNotEqual(0, wrongHint.ExitCode, wrongHint.Output);
        Assert.Contains("PKCS017", wrongHint.Output);

        var nestedHint = await BuildExternalGeneratedProjectAsync("NestedHint");
        Assert.AreNotEqual(0, nestedHint.ExitCode, nestedHint.Output);
        Assert.Contains("PKCS017", nestedHint.Output);

        var noHeader = await BuildExternalGeneratedProjectAsync("NoHeader");
        Assert.AreNotEqual(0, noHeader.ExitCode, noHeader.Output);
        Assert.Contains("PKCS017", noHeader.Output);

        var malformedHeader =
            await BuildExternalGeneratedProjectAsync("MalformedHeader");
        Assert.AreNotEqual(0, malformedHeader.ExitCode, malformedHeader.Output);
        Assert.Contains("PKCS017", malformedHeader.Output);

        var omittedPhysicalSource =
            await BuildExternalGeneratedProjectAsync("OmittedPhysicalSource");
        Assert.AreNotEqual(
            0,
            omittedPhysicalSource.ExitCode,
            omittedPhysicalSource.Output);
        Assert.Contains("PKCS158", omittedPhysicalSource.Output);

        var defaultItemExcludesOmission =
            await BuildExternalGeneratedProjectAsync(
                "DefaultItemExcludesOmission");
        Assert.AreNotEqual(
            0,
            defaultItemExcludesOmission.ExitCode,
            defaultItemExcludesOmission.Output);
        Assert.Contains("PKCS158", defaultItemExcludesOmission.Output);
    }

    [TestMethod]
    public async Task UnitTestFoldersMustMirrorAProductIntent()
    {
        var project = GetTestMirroringProjectPath();
        var misaligned = await BuildProjectAsync(project);

        Assert.AreNotEqual(0, misaligned.ExitCode, misaligned.Output);
        Assert.Contains("PKCS003", misaligned.Output);

        var concreteTestDependency = await BuildProjectAsync(
            project,
            "--property:GateMutation=ConcreteTestDependency");
        Assert.AreNotEqual(
            0,
            concreteTestDependency.ExitCode,
            concreteTestDependency.Output);
        Assert.Contains("PKCS016", concreteTestDependency.Output);

        var weakenedAnalysis = await BuildProjectAsync(
            project,
            "--property:GateMutation=MSTestAnalysisModeDisabled");
        Assert.AreNotEqual(0, weakenedAnalysis.ExitCode, weakenedAnalysis.Output);
        Assert.Contains("PKCS125", weakenedAnalysis.Output);

        var detachedAnalyzer = await BuildProjectAsync(
            project,
            "--property:GateMutation=RemoveMSTestAnalyzer");
        Assert.AreNotEqual(0, detachedAnalyzer.ExitCode, detachedAnalyzer.Output);
        Assert.Contains("PKCS142", detachedAnalyzer.Output);

        var futureTestProject = GetFutureTestMirroringProjectPath();
        var futureMisalignment = await BuildProjectAsync(futureTestProject);
        Assert.AreNotEqual(
            0,
            futureMisalignment.ExitCode,
            futureMisalignment.Output);
        Assert.Contains("PKCS003", futureMisalignment.Output);
    }

    [TestMethod]
    public async Task SuppressionLedgerIsSemanticExactAndFullyConsumed()
    {
        var approved = await BuildLedgerProbeAsync("ApprovedSuppression");
        Assert.AreEqual(0, approved.ExitCode, approved.Output);

        var approvedPragma = await BuildLedgerProbeAsync("ApprovedPragma");
        Assert.AreEqual(0, approvedPragma.ExitCode, approvedPragma.Output);

        var approvedNamedArguments =
            await BuildLedgerProbeAsync("ApprovedNamedArguments");
        Assert.AreEqual(
            0,
            approvedNamedArguments.ExitCode,
            approvedNamedArguments.Output);

        foreach (var (ledgerCase, diagnostic) in InvalidLedgerCases)
        {
            var result = await BuildLedgerProbeAsync(ledgerCase);
            Assert.AreNotEqual(
                0,
                result.ExitCode,
                $"{ledgerCase} unexpectedly passed.{Environment.NewLine}{result.Output}");
            Assert.Contains(diagnostic, result.Output);
        }

        foreach (var changedSuppression in new[]
                 {
                      "WidenedPragma",
                      "ChangedAttributeScope",
                      "InactiveRestore",
                      "ChangedAttributeTarget",
                  })
        {
            var result = await BuildLedgerProbeAsync(changedSuppression);
            Assert.AreNotEqual(0, result.ExitCode, result.Output);
            Assert.Contains("PKCS006", result.Output);
            Assert.Contains("PKCS013", result.Output);
        }
    }

    [TestMethod]
    public async Task Cs1701CompatibilityQuarantineIsExactAndRejectsToolchainDrift()
    {
        var unitTestProject = GetUnitTestProjectPath();
        var valid = await BuildProjectAsync(
            unitTestProject,
            "--no-restore",
            "--no-incremental");
        Assert.AreEqual(0, valid.ExitCode, valid.Output);

        var tamperingTargets = GetCs1701CompatibilityTamperingTargetsPath();
        foreach (var mutation in new[]
                 {
                     "WrongRuntimeIdentity",
                     "WrongPackageVersion",
                     "RawLowerTargetReference",
                 })
        {
            var result = await BuildProjectAsync(
                unitTestProject,
                "--no-restore",
                "--no-incremental",
                $"--property:CustomAfterMicrosoftCommonTargets={tamperingTargets}",
                $"--property:Cs1701CompatibilityMutation={mutation}");
            Assert.AreNotEqual(
                0,
                result.ExitCode,
                $"{mutation} unexpectedly passed.{Environment.NewLine}{result.Output}");
            Assert.Contains("PKCS174", result.Output);
        }

        var wrongDiagnostic = await BuildProjectAsync(
            unitTestProject,
            "--no-restore",
            "--no-incremental",
            $"--property:CustomAfterMicrosoftCommonTargets={tamperingTargets}",
            "--property:Cs1701CompatibilityMutation=WrongDiagnostic");
        Assert.AreNotEqual(0, wrongDiagnostic.ExitCode, wrongDiagnostic.Output);
        Assert.Contains("CS1701", wrongDiagnostic.Output);

        var wrongProject = await BuildProjectAsync(
            GetProbeProjectPath(),
            "--no-restore",
            "--no-incremental",
            "--property:GateCase=Valid",
            $"--property:CustomAfterMicrosoftCommonTargets={tamperingTargets}",
            "--property:Cs1701CompatibilityMutation=WrongProject");
        Assert.AreNotEqual(0, wrongProject.ExitCode, wrongProject.Output);
        Assert.Contains("PKCS174", wrongProject.Output);

        var cronosProject = GetCronosProjectPath();
        var validCronos = await BuildProjectAsync(
            cronosProject,
            "--no-restore",
            "--no-incremental");
        Assert.AreEqual(0, validCronos.ExitCode, validCronos.Output);
        foreach (var mutation in new[]
                 {
                     "WrongCronosRuntimeIdentity",
                     "WrongCronosReference",
                 })
        {
            var result = await BuildProjectAsync(
                cronosProject,
                "--no-restore",
                "--no-incremental",
                $"--property:CustomAfterMicrosoftCommonTargets={tamperingTargets}",
                $"--property:Cs1701CompatibilityMutation={mutation}");
            Assert.AreNotEqual(
                0,
                result.ExitCode,
                $"{mutation} unexpectedly passed.{Environment.NewLine}{result.Output}");
            Assert.Contains("PKCS174", result.Output);
        }

        var tUnitProject = GetObservatoryTestProjectPath();
        var validTUnit = await BuildProjectAsync(
            tUnitProject,
            "--no-restore",
            "--no-incremental");
        Assert.AreEqual(0, validTUnit.ExitCode, validTUnit.Output);
        foreach (var mutation in new[]
                 {
                     "WrongTUnitRuntimeIdentity",
                     "WrongTUnitReference",
                     "WrongTUnitFrameworkAsset",
                 })
        {
            var result = await BuildProjectAsync(
                tUnitProject,
                "--no-restore",
                "--no-incremental",
                $"--property:CustomAfterMicrosoftCommonTargets={tamperingTargets}",
                $"--property:Cs1701CompatibilityMutation={mutation}");
            Assert.AreNotEqual(
                0,
                result.ExitCode,
                $"{mutation} unexpectedly passed.{Environment.NewLine}{result.Output}");
            Assert.Contains("PKCS174", result.Output);
        }
    }

    [TestMethod]
    public async Task AcceptanceCommandsCannotSkipTheCurrentGateBuild()
    {
        var artifactsProject = GetArtifactsProjectPath();
        var temporaryDirectory = Directory.CreateTempSubdirectory(
            "program-kit-acceptance-");
        try
        {
            var ordinaryPackageOutput = Directory.CreateDirectory(
                Path.Combine(
                    temporaryDirectory.FullName,
                    "ordinary-package"));
            var ordinaryPack = await RunDotNetProjectCommandAsync(
                "pack",
                artifactsProject,
                "--configuration",
                "Release",
                "--no-restore",
                $"--output={ordinaryPackageOutput.FullName}");
            Assert.AreEqual(0, ordinaryPack.ExitCode, ordinaryPack.Output);
            Assert.HasCount(
                1,
                Directory.GetFiles(
                    ordinaryPackageOutput.FullName,
                    "*.nupkg",
                    SearchOption.TopDirectoryOnly));

            var generatedPackageOutput = Directory.CreateDirectory(
                Path.Combine(
                    temporaryDirectory.FullName,
                    "generate-package-on-build"));
            var generatedPackage = await BuildProjectAsync(
                artifactsProject,
                "--no-restore",
                "--no-incremental",
                "--property:GeneratePackageOnBuild=true",
                $"--property:PackageOutputPath={generatedPackageOutput.FullName}");
            Assert.AreEqual(
                0,
                generatedPackage.ExitCode,
                generatedPackage.Output);
            Assert.HasCount(
                1,
                Directory.GetFiles(
                    generatedPackageOutput.FullName,
                    "*.nupkg",
                    SearchOption.TopDirectoryOnly));

            var noBuildPackageOutput = Directory.CreateDirectory(
                Path.Combine(
                    temporaryDirectory.FullName,
                    "no-build-package"));
            var noBuildPack = await RunDotNetProjectCommandAsync(
                "pack",
                artifactsProject,
                "--configuration",
                "Release",
                "--no-restore",
                "--no-build",
                $"--output={noBuildPackageOutput.FullName}");
            Assert.AreNotEqual(0, noBuildPack.ExitCode, noBuildPack.Output);
            Assert.Contains("PKCS152", noBuildPack.Output);
            AssertDirectoryContainsNoFiles(noBuildPackageOutput);

            var directNuspecOutput = Directory.CreateDirectory(
                Path.Combine(
                    temporaryDirectory.FullName,
                    "direct-nuspec"));
            var directNuspec = await RunDotNetProjectCommandAsync(
                "msbuild",
                artifactsProject,
                "--nologo",
                "--target:GenerateNuspec",
                "--property:Configuration=Release",
                "--property:NoRestore=true",
                $"--property:PackageOutputPath={directNuspecOutput.FullName}",
                $"--property:NuspecOutputPath={directNuspecOutput.FullName}");
            Assert.AreNotEqual(
                0,
                directNuspec.ExitCode,
                directNuspec.Output);
            Assert.Contains("PKCS177", directNuspec.Output);
            AssertDirectoryContainsNoFiles(directNuspecOutput);

            var ordinaryPublishOutput = Directory.CreateDirectory(
                Path.Combine(
                    temporaryDirectory.FullName,
                    "ordinary-publish"));
            var ordinaryPublish = await RunDotNetProjectCommandAsync(
                "publish",
                artifactsProject,
                "--configuration",
                "Release",
                "--no-restore",
                $"--output={ordinaryPublishOutput.FullName}");
            Assert.AreEqual(
                0,
                ordinaryPublish.ExitCode,
                ordinaryPublish.Output);
            Assert.IsTrue(
                File.Exists(
                    Path.Combine(
                        ordinaryPublishOutput.FullName,
                        "Orbyss.ProgramKit.Artifacts.dll")),
                ordinaryPublish.Output);

            var noBuildPublishOutput = Directory.CreateDirectory(
                Path.Combine(
                    temporaryDirectory.FullName,
                    "no-build-publish"));
            var noBuildPublish = await RunDotNetProjectCommandAsync(
                "publish",
                artifactsProject,
                "--configuration",
                "Release",
                "--no-restore",
                "--no-build",
                $"--output={noBuildPublishOutput.FullName}");
            Assert.AreNotEqual(
                0,
                noBuildPublish.ExitCode,
                noBuildPublish.Output);
            Assert.Contains("PKCS153", noBuildPublish.Output);
            AssertDirectoryContainsNoFiles(noBuildPublishOutput);

            foreach (var target in new[]
                     {
                         "PrepareForPublish",
                         "ComputeAndCopyFilesToPublishDirectory",
                     })
            {
                var directPublishOutput = Directory.CreateDirectory(
                    Path.Combine(
                        temporaryDirectory.FullName,
                        target));
                var directPublish = await RunDotNetProjectCommandAsync(
                    "msbuild",
                    artifactsProject,
                    "--nologo",
                    $"--target:{target}",
                    "--property:Configuration=Release",
                    "--property:NoRestore=true",
                    $"--property:PublishDir={directPublishOutput.FullName}");
                Assert.AreNotEqual(
                    0,
                    directPublish.ExitCode,
                    directPublish.Output);
                Assert.Contains("PKCS178", directPublish.Output);
                AssertDirectoryContainsNoFiles(directPublishOutput);
            }

            var designTimePack = await RunDotNetProjectCommandAsync(
                "pack",
                artifactsProject,
                "--configuration",
                "Release",
                "--no-restore",
                "--property:DesignTimeBuild=true",
                "--property:BuildingProject=false",
                "--property:SkipCompilerExecution=true");
            Assert.AreNotEqual(
                0,
                designTimePack.ExitCode,
                designTimePack.Output);
            Assert.Contains("PKCS172", designTimePack.Output);

            var designTimePublish = await RunDotNetProjectCommandAsync(
                "publish",
                artifactsProject,
                "--configuration",
                "Release",
                "--no-restore",
                "--property:DesignTimeBuild=true",
                "--property:BuildingProject=false",
                "--property:SkipCompilerExecution=true");
            Assert.AreNotEqual(
                0,
                designTimePublish.ExitCode,
                designTimePublish.Output);
            Assert.Contains("PKCS172", designTimePublish.Output);
        }
        finally
        {
            DeleteTemporaryDirectory(temporaryDirectory);
        }
    }

    [TestMethod]
    public async Task PrivateGateDecisionStateCannotBeSpoofed()
    {
        var project = GetProbeProjectPath();
        var receiptRoot = Path.Combine(
            Path.GetDirectoryName(project)!,
            "obj",
            "ProgramKitCompilerGenerated",
            "net10.0");
        var receiptsBeforeNonceBuild = Directory.Exists(receiptRoot)
            ? Directory
                .GetFiles(
                    receiptRoot,
                    "ProgramKitCompilerInvocationReceipt.*.cs",
                    SearchOption.AllDirectories)
                .ToHashSet(StringComparer.OrdinalIgnoreCase)
            : new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var spoofedNonce = new string('0', 32);
        var nonce = await BuildProjectAsync(
            project,
            "--no-restore",
            "--property:GateCase=Valid",
            $"--property:ProgramKitCompilerInvocationNonce={spoofedNonce}",
            $"--property:_ProgramKitExpectedCompilerInvocationNonce={spoofedNonce}");
        Assert.AreEqual(0, nonce.ExitCode, nonce.Output);
        var nonceReceipts = Directory
            .GetFiles(
                receiptRoot,
                "ProgramKitCompilerInvocationReceipt.*.cs",
                SearchOption.AllDirectories)
            .Where(path => !receiptsBeforeNonceBuild.Contains(path))
            .ToArray();
        Assert.HasCount(1, nonceReceipts);
        Assert.DoesNotContain(spoofedNonce, nonceReceipts[0]);

        var gatePath = await BuildProjectAsync(
            project,
            "--property:GateCase=Valid",
            "--property:ProgramKitCSharpGateProjectPath=C:\\spoof\\gate.csproj",
            "--property:_ProgramKitExpectedCSharpGateProjectPath=C:\\spoof\\gate.csproj");
        Assert.AreNotEqual(0, gatePath.ExitCode, gatePath.Output);
        Assert.Contains("PKCS127", gatePath.Output);

        var assemblyPath = await BuildProjectAsync(
            project,
            "--property:GateCase=Valid",
            "--property:ProgramKitCSharpGateAssemblyPath=C:\\spoof\\gate.dll",
            "--property:_ProgramKitExpectedCSharpGateAssemblyPath=C:\\spoof\\gate.dll");
        Assert.AreNotEqual(0, assemblyPath.ExitCode, assemblyPath.Output);
        Assert.Contains("PKCS128", assemblyPath.Output);

        var ledgerPath = await BuildProjectAsync(
            project,
            "--property:GateCase=Valid",
            "--property:ProgramKitWarningApprovalLedgerPath=C:\\spoof\\ledger.tsv",
            "--property:_ProgramKitExpectedWarningApprovalLedgerPath=C:\\spoof\\ledger.tsv");
        Assert.AreNotEqual(0, ledgerPath.ExitCode, ledgerPath.Output);
        Assert.Contains("PKCS129", ledgerPath.Output);

        var generatedProbePath = await BuildProjectAsync(
            project,
            "--property:GateCase=Valid",
            "--property:ProgramKitGeneratedSourceProbeProject=C:\\spoof\\generator.csproj",
            "--property:_ProgramKitExpectedGeneratedSourceProbeProjectPath=C:\\spoof\\generator.csproj");
        Assert.AreNotEqual(
            0,
            generatedProbePath.ExitCode,
            generatedProbePath.Output);
        Assert.Contains("PKCS155", generatedProbePath.Output);

        var privateRoots = await BuildProjectAsync(
            project,
            "--property:GateCase=Valid",
            "--property:_ProgramKitFrameworkAnalyzerRoot=C:\\spoof\\analyzers\\",
            "--property:_ProgramKitNetAnalyzerPath=C:\\spoof\\net-analyzer.dll",
            "--property:_ProgramKitIntermediateRoot=C:\\spoof\\obj");
        Assert.AreEqual(0, privateRoots.ExitCode, privateRoots.Output);

        var selfValidationInternals = await BuildProjectAsync(
            GetGateProjectPath(),
            "--no-restore",
            "--property:_ProgramKitDotNetHostPath=C:\\spoof\\dotnet.exe",
            "--property:_ProgramKitSelfValidationAnalyzerPath=C:\\spoof\\gate.dll",
            "--property:_ProgramKitSelfValidationInvocationDirectory=C:\\spoof\\tokens");
        Assert.AreEqual(
            0,
            selfValidationInternals.ExitCode,
            selfValidationInternals.Output);
        Assert.Contains(
            "Running mandatory Program Kit C# gate self-validation.",
            selfValidationInternals.Output);
    }

    [TestMethod]
    public async Task PhysicalOwnedSourcesCannotBeRemovedFromCompile()
    {
        var project = GetArtifactsProjectPath();
        var defaultItems = await BuildProjectAsync(
            project,
            "--property:EnableDefaultItems=false");
        Assert.AreNotEqual(0, defaultItems.ExitCode, defaultItems.Output);
        Assert.Contains("PKCS156", defaultItems.Output);

        var defaultCompileItems = await BuildProjectAsync(
            project,
            "--property:EnableDefaultCompileItems=false");
        Assert.AreNotEqual(
            0,
            defaultCompileItems.ExitCode,
            defaultCompileItems.Output);
        Assert.Contains("PKCS157", defaultCompileItems.Output);

        var removeTarget = Path.Combine(
            Path.GetDirectoryName(GetProbeProjectPath())!,
            "Configurations",
            "RemoveOwnedSource.targets");
        var removedSource = await BuildProjectAsync(
            project,
            $"--property:CustomAfterMicrosoftCommonTargets={removeTarget}",
            "--property:_ProgramKitIsOwnedSourceProject=false");
        Assert.AreNotEqual(0, removedSource.ExitCode, removedSource.Output);
        Assert.Contains("PKCS158", removedSource.Output);
    }

    private static async Task<GateBuildResult> BuildProbeAsync(
        string gateCase,
        string configuration = "Release",
        string? property = null,
        string? value = null,
        bool reuseValidatedGate = true)
    {
        var project = GetProbeProjectPath();
        Assert.IsTrue(File.Exists(project), project);

        var arguments = new List<string>
        {
            "--no-restore",
            $"--property:GateCase={gateCase}",
        };
        if (reuseValidatedGate)
        {
            arguments.Add(
                $"--property:ProgramKitConformanceValidatedGateDigest={ReadValidatedGateDigest(configuration)}");
        }
        if (property is not null)
        {
            arguments.Add($"--property:{property}={value}");
        }

        return await BuildProjectAsync(
            project,
            configuration,
            [.. arguments]);
    }

    private static Task<GateBuildResult> BuildProbeMutationAsync(
        string mutation,
        string configuration = "Release") =>
        BuildProjectAsync(
            GetProbeProjectPath(),
            configuration,
            [
                "--no-restore",
                "--property:GateCase=Valid",
                $"--property:GateMutation={mutation}",
                .. ConformanceGateReuseArguments(mutation, configuration),
            ]);

    private static string[] ConformanceGateReuseArguments(
        string mutation,
        string configuration) =>
        mutation is "BuildReferenceFalse" or "TargetsGetTargetPath"
            ? []
            :
            [
                $"--property:ProgramKitConformanceValidatedGateDigest={ReadValidatedGateDigest(configuration)}",
            ];

    private static string ReadValidatedGateDigest(string configuration)
    {
        var receipt = GetValidatedGateReceiptPath(configuration);
        Assert.IsTrue(File.Exists(receipt), receipt);
        return File.ReadAllText(receipt);
    }

    private static IEnumerable<string> GateConfigurations()
    {
        yield return "Release";
        for (var lane = 0; lane < MatrixLaneCount; lane++)
        {
            yield return $"GateMatrix{lane}";
        }
    }

    private static async Task<GateBuildResult[]> RunBuildMatrixAsync<T>(
        IReadOnlyList<T> cases,
        Func<T, string, Task<GateBuildResult>> build)
    {
        var results = new GateBuildResult[cases.Count];
        var lanes = Enumerable
            .Range(0, Math.Min(MatrixLaneCount, cases.Count))
            .Select(RunLaneAsync);

        await Task.WhenAll(lanes);
        return results;

        async Task RunLaneAsync(int lane)
        {
            var configuration = $"GateMatrix{lane}";
            for (var index = lane; index < cases.Count; index += MatrixLaneCount)
            {
                results[index] = await build(cases[index], configuration);
            }
        }
    }

    private static async Task<GateBuildResult> BuildLedgerProbeAsync(
        string ledgerCase)
    {
        var programKitRoot = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit");
        var sourceProject = GetLedgerProbeProjectPath();
        var sourceRoot = Path.GetDirectoryName(sourceProject)!;
        var temporaryDirectory = Directory.CreateTempSubdirectory(
            "program-kit-ledger-gate-");
        try
        {
            var temporaryProject = Path.Combine(
                temporaryDirectory.FullName,
                "DirectAnalyzerProbe.csproj");
            var temporaryConfigurationDirectory = Directory.CreateDirectory(
                Path.Combine(
                    temporaryDirectory.FullName,
                    "Configuration",
                    ledgerCase));
            var temporaryLedgerDirectory = Directory.CreateDirectory(
                Path.Combine(
                    temporaryDirectory.FullName,
                    "Ledgers",
                    ledgerCase));
            File.Copy(sourceProject, temporaryProject);
            File.Copy(
                Path.Combine(sourceRoot, "packages.lock.json"),
                Path.Combine(
                    temporaryDirectory.FullName,
                    "packages.lock.json"));
            foreach (var sourceFile in Directory.EnumerateFiles(
                         Path.Combine(
                             sourceRoot,
                             "Configuration",
                             ledgerCase),
                         "*.cs"))
            {
                File.Copy(
                    sourceFile,
                    Path.Combine(
                        temporaryConfigurationDirectory.FullName,
                        Path.GetFileName(sourceFile)));
            }

            File.Copy(
                Path.Combine(
                    sourceRoot,
                    "Ledgers",
                    ledgerCase,
                    "approved-warning-suppressions.tsv"),
                Path.Combine(
                    temporaryLedgerDirectory.FullName,
                    "approved-warning-suppressions.tsv"));
            return await BuildProjectAsync(
                temporaryProject,
                $"--property:ProgramKitBuildRoot={programKitRoot}",
                $"--property:ProgramKitLedgerCase={ledgerCase}");
        }
        finally
        {
            DeleteTemporaryDirectory(temporaryDirectory);
        }
    }

    private static async Task<GateBuildResult> BuildExternalGeneratedProjectAsync(
        string gateCase,
        bool useGeneratedAncestor = false)
    {
        var fixtureDirectory = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "CSharpGate");
        var template = Path.Combine(
            fixtureDirectory,
            "ExternalGeneratedProject",
            "GeneratedHost.csproj");
        var generator = Path.Combine(
            fixtureDirectory,
            "GeneratedSource",
            "Generator",
            "GeneratedSourceProbe.csproj");
        var programKitRoot = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit");
        Assert.IsTrue(File.Exists(template), template);
        Assert.IsTrue(File.Exists(generator), generator);

        var temporaryDirectory = Directory.CreateTempSubdirectory(
            "program-kit-csharp-gate-");
        try
        {
            var externalProjectDirectory = useGeneratedAncestor
                ? Directory.CreateDirectory(
                    Path.Combine(
                        temporaryDirectory.FullName,
                        "ProgramKitGenerated",
                        "AncestorProject")).FullName
                : temporaryDirectory.FullName;
            var externalProject = Path.Combine(
                externalProjectDirectory,
                "GeneratedHost.csproj");
            File.Copy(template, externalProject);
            var templateSource = Path.Combine(
                Path.GetDirectoryName(template)!,
                "Hosting",
                "OwnedHostMarker.cs");
            var externalSourceDirectory = Directory.CreateDirectory(
                Path.Combine(externalProjectDirectory, "Hosting"));
            File.Copy(
                templateSource,
                Path.Combine(
                    externalSourceDirectory.FullName,
                    "OwnedHostMarker.cs"));

            return await BuildProjectAsync(
                externalProject,
                $"--property:ProgramKitBuildRoot={programKitRoot}",
                $"--property:ProgramKitGeneratedSourceProbeProject={generator}",
                $"--property:GeneratedGateCase={gateCase}");
        }
        finally
        {
            DeleteTemporaryDirectory(temporaryDirectory);
        }
    }

    private static string CreateExternalGeneratedProject(
        DirectoryInfo temporaryDirectory,
        string directoryName)
    {
        var fixtureDirectory = Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "CSharpGate",
            "ExternalGeneratedProject");
        var projectDirectory = Directory.CreateDirectory(
            Path.Combine(
                temporaryDirectory.FullName,
                directoryName));
        var hostingDirectory = Directory.CreateDirectory(
            Path.Combine(
                projectDirectory.FullName,
                "Hosting"));
        File.Copy(
            Path.Combine(fixtureDirectory, "GeneratedHost.csproj"),
            Path.Combine(
                projectDirectory.FullName,
                "GeneratedHost.csproj"));
        File.Copy(
            Path.Combine(fixtureDirectory, "packages.lock.json"),
            Path.Combine(
                projectDirectory.FullName,
                "packages.lock.json"));
        File.Copy(
            Path.Combine(
                fixtureDirectory,
                "Hosting",
                "OwnedHostMarker.cs"),
            Path.Combine(
                hostingDirectory.FullName,
                "OwnedHostMarker.cs"));
        return Path.Combine(
            projectDirectory.FullName,
            "GeneratedHost.csproj");
    }

    private static void AssertCompilerInvocationReceipt(
        string receipt,
        HashSet<string> observedNonces)
    {
        var fileName = Path.GetFileName(receipt);
        const string prefix = "ProgramKitCompilerInvocationReceipt.";
        const string suffix = ".cs";
        Assert.IsTrue(
            fileName.StartsWith(prefix, StringComparison.Ordinal),
            fileName);
        Assert.IsTrue(
            fileName.EndsWith(suffix, StringComparison.Ordinal),
            fileName);
        var nonce = fileName[prefix.Length..^suffix.Length];
        Assert.IsTrue(
            nonce.Length == 32 &&
            nonce.All(character =>
                character is >= '0' and <= '9' or
                >= 'a' and <= 'f'),
            fileName);
        Assert.IsTrue(observedNonces.Add(nonce), fileName);
        Assert.Contains(
            $"{Path.DirectorySeparatorChar}{nonce}" +
            Path.DirectorySeparatorChar,
            receipt);
        Assert.AreSequenceEqual(
            [
                "// <auto-generated program-kit>",
                $"// compiler-executed:{nonce}",
            ],
            File.ReadAllLines(receipt));
    }

    private static void DeleteTemporaryDirectory(
        DirectoryInfo temporaryDirectory)
    {
        var temporaryRoot = Path.GetFullPath(Path.GetTempPath());
        var resolvedDirectory = Path.GetFullPath(
            temporaryDirectory.FullName);
        Assert.IsTrue(
            resolvedDirectory.StartsWith(
                temporaryRoot,
                StringComparison.OrdinalIgnoreCase),
            resolvedDirectory);
        temporaryDirectory.Refresh();
        if (temporaryDirectory.Exists)
        {
            temporaryDirectory.Delete(recursive: true);
        }
    }

    private static void AssertDirectoryContainsNoFiles(
        DirectoryInfo directory) =>
        Assert.IsEmpty(
            Directory.EnumerateFiles(
                directory.FullName,
                "*",
                SearchOption.AllDirectories),
            directory.FullName);

    private static string GetGateProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tools",
            "Orbyss.ProgramKit.CSharpGate",
            "Orbyss.ProgramKit.CSharpGate.csproj");

    private static string GetGateAssemblyPath(string configuration) =>
        Path.Combine(
            Path.GetDirectoryName(GetGateProjectPath())!,
            "bin",
            configuration,
            "net10.0",
            "Orbyss.ProgramKit.CSharpGate.dll");

    private static string GetValidatedGateReceiptPath(string configuration) =>
        Path.Combine(
            Path.GetDirectoryName(GetProbeProjectPath())!,
            "obj",
            "conformance",
            $"validated-gate.{configuration}.sha256");

    private static string GetArtifactsProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "src",
            "Orbyss.ProgramKit.Artifacts",
            "Orbyss.ProgramKit.Artifacts.csproj");

    private static string GetUnitTestProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.UnitTests",
            "Orbyss.ProgramKit.UnitTests.csproj");

    private static string GetCronosProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "src",
            "Orbyss.ProgramKit.Tasks.Schedules.Cronos",
            "Orbyss.ProgramKit.Tasks.Schedules.Cronos.csproj");

    private static string GetObservatoryTestProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "fixtures",
            "observatory-scheduling",
            "tests",
            "ObservatoryScheduling.Tests",
            "ObservatoryScheduling.Tests.csproj");

    private static string GetSolutionPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "ProgramKit.sln");

    private static string GetCs1701CompatibilityTamperingTargetsPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "CSharpGate",
            "Configurations",
            "Cs1701CompatibilityQuarantineTampering.targets");

    private static string GetProbeProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "CSharpGate",
            "CSharpGateProbe.csproj");

    private static string GetTestMirroringProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "CSharpGate",
            "TestMirroring",
            "Orbyss.ProgramKit.UnitTests.csproj");

    private static string GetFutureTestMirroringProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "CSharpGate",
            "FutureTestMirroring",
            "Orbyss.ProgramKit.Artifacts.UnitTests.csproj");

    private static string GetLedgerProbeProjectPath() =>
        Path.Combine(
            ConformanceInputs.RepositoryRoot,
            "program-kit",
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "CSharpGate",
            "Ledger",
            "DirectAnalyzerProbe.csproj");

    private static Task<GateBuildResult> BuildProjectAsync(
        string project,
        params string[] additionalArguments)
        =>
        BuildProjectAsync(
            project,
            "Release",
            additionalArguments);

    private static Task<GateBuildResult> BuildProjectAsync(
        string project,
        string configuration,
        IReadOnlyCollection<string> additionalArguments)
    {
        var arguments = new List<string>
        {
            "--configuration",
            configuration,
            "--nologo",
        };
        arguments.AddRange(additionalArguments);
        return RunDotNetProjectCommandAsync(
            "build",
            project,
            [.. arguments]);
    }

    private static Task<GateBuildResult> RestoreProjectAsync(
        string project,
        params string[] additionalArguments)
    {
        var arguments = new List<string>
        {
            "--nologo",
        };
        arguments.AddRange(additionalArguments);
        return RunDotNetProjectCommandAsync(
            "restore",
            project,
            [.. arguments]);
    }

    private static async Task<GateBuildResult> RunDotNetProjectCommandAsync(
        string command,
        string project,
        params string[] additionalArguments)
    {
        Assert.IsTrue(File.Exists(project), project);
        var startInfo = new ProcessStartInfo
        {
            FileName = Environment.GetEnvironmentVariable("DOTNET_HOST_PATH") ?? "dotnet",
            WorkingDirectory = Path.GetDirectoryName(project)!,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        startInfo.ArgumentList.Add(command);
        startInfo.ArgumentList.Add(project);
        foreach (var argument in additionalArguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start the .NET SDK process.");
        var standardOutput = process.StandardOutput.ReadToEndAsync();
        var standardError = process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        return new GateBuildResult(
            process.ExitCode,
            string.Concat(
                await standardOutput,
                Environment.NewLine,
                await standardError));
    }
}
