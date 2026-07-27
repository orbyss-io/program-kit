using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Decisions;

/// <summary>Every artifact kind supported by the baseline decision contract.</summary>
public enum SupportedArtifactKind
{
    /// <summary>Human-authored executable or library source.</summary>
    SourceCode,

    /// <summary>Build-project configuration.</summary>
    ProjectConfiguration,

    /// <summary>Package identity, dependency, or packing configuration.</summary>
    PackageConfiguration,

    /// <summary>A machine-readable structural contract.</summary>
    Schema,

    /// <summary>A durable value governed by a schema.</summary>
    SchemaInstance,

    /// <summary>A runtime or design-time configuration value.</summary>
    Configuration,

    /// <summary>A generated manifest.</summary>
    GeneratedManifest,

    /// <summary>A generated catalog.</summary>
    GeneratedCatalog,

    /// <summary>A generated navigation index.</summary>
    GeneratedIndex,

    /// <summary>A provider-neutral agent instruction.</summary>
    ProviderNeutralAgentInstruction,

    /// <summary>A provider-neutral, human-started agent capability.</summary>
    ProviderNeutralAgentCapability,

    /// <summary>A document intended for human explanation.</summary>
    HumanDocument,

    /// <summary>A supplied human decision record.</summary>
    HumanDecisionRecord,

    /// <summary>A reusable test specification.</summary>
    TestSpecification,

    /// <summary>A bounded test execution profile.</summary>
    TestProfile,

    /// <summary>Exact test input or expected-output data.</summary>
    TestFixture,

    /// <summary>Source code generated from canonical inputs.</summary>
    GeneratedCode,

    /// <summary>A human-readable document generated from canonical inputs.</summary>
    GeneratedDocument,

    /// <summary>Ephemeral state named and bounded by a contract.</summary>
    ContractDefinedEphemeralState,

    /// <summary>An OpenAPI integration document.</summary>
    OpenApiDocument,

    /// <summary>An Open Console integration document.</summary>
    OpenConsoleDocument,

    /// <summary>An Open Worker integration document.</summary>
    OpenWorkerDocument,

    /// <summary>An independently versioned component description.</summary>
    VersionComponent,

    /// <summary>An exact observed and target version selection.</summary>
    VersionSelection,

    /// <summary>A typed version-dependency graph.</summary>
    VersionMap,

    /// <summary>An explicit version migration definition.</summary>
    MigrationDefinition,

    /// <summary>A closed migration-impact assessment.</summary>
    MigrationImpactAssessment,

    /// <summary>An immutable JSON serialization profile.</summary>
    JsonSerializationProfile,

    /// <summary>A typed JSON serialization contribution.</summary>
    JsonSerializationContribution,

    /// <summary>Opaque canonical JSON bytes at an approved untyped boundary.</summary>
    CanonicalJsonValue,

    /// <summary>A stable requested-work definition.</summary>
    TaskDefinition,

    /// <summary>A provider-neutral task schedule descriptor.</summary>
    TaskScheduleDescriptor,

    /// <summary>An exact host composition selection.</summary>
    HostComposition,

    /// <summary>A manifest of a deterministic local application publish.</summary>
    LocalPublishManifest,

    /// <summary>Generated operational health configuration.</summary>
    GeneratedHealthConfiguration
}
