using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture;

/// <summary>
/// Classifies the semantic owner responsible for an artifact kind. This is an
/// ownership classification, not an implementation layer or storage location.
/// </summary>
public enum ArtifactOwnershipClassification
{
    /// <summary>A domain owns semantic meaning and public behavior.</summary>
    DomainSemantic,

    /// <summary>A project or package owns a build and distribution boundary.</summary>
    BuildBoundary,

    /// <summary>A producer owns a deterministic projection of canonical inputs.</summary>
    GeneratedProjection,

    /// <summary>A human-started capability owner governs agent procedure.</summary>
    AgentProcedure,

    /// <summary>A human authority owns an explanation or decision record.</summary>
    HumanAuthority,

    /// <summary>A quality owner governs reusable verification meaning.</summary>
    Quality,

    /// <summary>A versioned boundary owner governs compatibility selection.</summary>
    Versioning,

    /// <summary>An impacted semantic or deployable boundary owns migration.</summary>
    Migration,

    /// <summary>A serialization owner governs an exact wire representation.</summary>
    Serialization,

    /// <summary>A domain owns requested-work and schedule meaning.</summary>
    Tasking,

    /// <summary>A host owns selected composition and operational configuration.</summary>
    HostComposition,

    /// <summary>A contract owner bounds state that is deliberately not durable.</summary>
    EphemeralState
}

/// <summary>
/// The canonical identity and owner PKID kinds for one supported artifact kind.
/// </summary>
public sealed record SupportedArtifactKindOwnership(
    SupportedArtifactKind ArtifactKind,
    ArtifactOwnershipClassification Classification,
    ImmutableArray<string> ArtifactIdentityKinds,
    ImmutableArray<string> OwnerIdentityKinds,
    string CanonicalOwnership);

/// <summary>
/// Resolves every supported artifact kind to one deterministic canonical
/// ownership rule. The rules prevent representation names from replacing
/// semantic identities: for example, a schema artifact has a
/// <c>pkid:schema</c> identity and cannot masquerade as a
/// <c>pkid:contract</c>. A typed contract may instead select
/// <see cref="SupportedArtifactKind.SchemaInstance"/>.
/// </summary>
public static class SupportedArtifactKindOwnershipResolver
{
    private static readonly ImmutableArray<string> DomainOwners = ["domain"];
    private static readonly ImmutableArray<string> BuildOwners = ["project", "package"];
    private static readonly ImmutableArray<string> ProjectionOwners =
        ["project", "package", "host", "capability"];
    private static readonly ImmutableArray<string> AgentOwners = ["capability", "project", "package"];
    private static readonly ImmutableArray<string> HumanOwners = ["approval", "domain", "capability"];
    private static readonly ImmutableArray<string> QualityOwners = ["test", "project", "package"];
    private static readonly ImmutableArray<string> VersionOwners =
        ["domain", "project", "package", "host"];
    private static readonly ImmutableArray<string> MigrationOwners =
        ["domain", "project", "package", "host"];
    private static readonly ImmutableArray<string> SerializationOwners = ["domain", "package"];
    private static readonly ImmutableArray<string> HostOwners = ["host", "project", "package"];

    private static readonly ImmutableArray<SupportedArtifactKindOwnership> Rules =
    [
        Rule(
            SupportedArtifactKind.SourceCode,
            ArtifactOwnershipClassification.BuildBoundary,
            ["project", "ai-artifact"],
            BuildOwners,
            "The source project owns human-authored source code."),
        Rule(
            SupportedArtifactKind.ProjectConfiguration,
            ArtifactOwnershipClassification.BuildBoundary,
            ["project"],
            BuildOwners,
            "The configured project owns project configuration."),
        Rule(
            SupportedArtifactKind.PackageConfiguration,
            ArtifactOwnershipClassification.BuildBoundary,
            ["package"],
            BuildOwners,
            "The independently versioned package owns package configuration."),
        Rule(
            SupportedArtifactKind.Schema,
            ArtifactOwnershipClassification.DomainSemantic,
            ["schema"],
            ["domain", "package"],
            "A schema identity owns serialized structure; it may describe but never replace a contract identity."),
        Rule(
            SupportedArtifactKind.SchemaInstance,
            ArtifactOwnershipClassification.DomainSemantic,
            [
                "contract",
                "design",
                "plan",
                "configuration",
                "catalog",
                "approval",
                "receipt",
                "profile",
                "capability-snapshot",
                "fixture",
                "task-definition",
                "task-schedule",
                "version-map",
                "version-selection",
                "migration",
                "host",
            ],
            ["domain", "project", "package", "host", "capability"],
            "The semantic subject owns a typed value governed by a separately identified schema."),
        Rule(
            SupportedArtifactKind.Configuration,
            ArtifactOwnershipClassification.DomainSemantic,
            ["configuration", "profile"],
            ["domain", "project", "package", "host"],
            "The configured semantic or host boundary owns configuration intent."),
        Rule(
            SupportedArtifactKind.GeneratedManifest,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["manifest", "catalog"],
            ProjectionOwners,
            "The deterministic producer owns a generated manifest projection."),
        Rule(
            SupportedArtifactKind.GeneratedCatalog,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["catalog"],
            ProjectionOwners,
            "The deterministic producer owns a generated catalog projection."),
        Rule(
            SupportedArtifactKind.GeneratedIndex,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["catalog"],
            ProjectionOwners,
            "The deterministic producer owns a generated navigation index."),
        Rule(
            SupportedArtifactKind.ProviderNeutralAgentInstruction,
            ArtifactOwnershipClassification.AgentProcedure,
            ["ai-artifact"],
            AgentOwners,
            "The human-started capability owner governs provider-neutral agent instruction."),
        Rule(
            SupportedArtifactKind.ProviderNeutralAgentCapability,
            ArtifactOwnershipClassification.AgentProcedure,
            ["capability"],
            AgentOwners,
            "The capability identity owns its bounded provider-neutral procedure."),
        Rule(
            SupportedArtifactKind.HumanDocument,
            ArtifactOwnershipClassification.HumanAuthority,
            ["ai-artifact", "design", "plan"],
            HumanOwners,
            "The semantic or human authority owner governs explanatory material."),
        Rule(
            SupportedArtifactKind.HumanDecisionRecord,
            ArtifactOwnershipClassification.HumanAuthority,
            ["approval", "ai-artifact"],
            HumanOwners,
            "The supplied human authority owns its decision record."),
        Rule(
            SupportedArtifactKind.TestSpecification,
            ArtifactOwnershipClassification.Quality,
            ["test"],
            QualityOwners,
            "The quality owner governs reusable verification meaning."),
        Rule(
            SupportedArtifactKind.TestProfile,
            ArtifactOwnershipClassification.Quality,
            ["profile"],
            QualityOwners,
            "The quality owner governs a bounded execution profile."),
        Rule(
            SupportedArtifactKind.TestFixture,
            ArtifactOwnershipClassification.Quality,
            ["fixture"],
            QualityOwners,
            "The quality owner governs exact fixture inputs and expected outputs."),
        Rule(
            SupportedArtifactKind.GeneratedCode,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["project", "ai-artifact"],
            ProjectionOwners,
            "The selected generator owner governs code projected from canonical inputs."),
        Rule(
            SupportedArtifactKind.GeneratedDocument,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["ai-artifact", "catalog"],
            ProjectionOwners,
            "The selected generator owner governs a human-readable projection."),
        Rule(
            SupportedArtifactKind.ContractDefinedEphemeralState,
            ArtifactOwnershipClassification.EphemeralState,
            ["ephemeral-state"],
            ["domain", "host"],
            "The contract or host owner bounds state that is never a canonical source instance."),
        Rule(
            SupportedArtifactKind.OpenApiDocument,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["open-api-document"],
            HostOwners,
            "The API host owns its projection of selected operation contracts."),
        Rule(
            SupportedArtifactKind.OpenConsoleDocument,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["open-console-document"],
            HostOwners,
            "The Console host owns its projection of selected operation contracts."),
        Rule(
            SupportedArtifactKind.OpenWorkerDocument,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["open-worker-document"],
            HostOwners,
            "The Worker host owns its projection of selected operation contracts."),
        Rule(
            SupportedArtifactKind.VersionComponent,
            ArtifactOwnershipClassification.Versioning,
            ["version-component"],
            VersionOwners,
            "The independently versioned boundary owns its component manifest."),
        Rule(
            SupportedArtifactKind.VersionSelection,
            ArtifactOwnershipClassification.Versioning,
            ["version-selection"],
            VersionOwners,
            "The selecting boundary owns exact observed and human-selected target revisions."),
        Rule(
            SupportedArtifactKind.VersionMap,
            ArtifactOwnershipClassification.Versioning,
            ["version-map"],
            VersionOwners,
            "The architecture or composition owner owns the typed dependency map."),
        Rule(
            SupportedArtifactKind.MigrationDefinition,
            ArtifactOwnershipClassification.Migration,
            ["migration"],
            MigrationOwners,
            "The changed semantic boundary owns its explicit migration definition."),
        Rule(
            SupportedArtifactKind.MigrationImpactAssessment,
            ArtifactOwnershipClassification.Migration,
            ["migration"],
            MigrationOwners,
            "The impacted migration cohort owns its closed impact assessment."),
        Rule(
            SupportedArtifactKind.JsonSerializationProfile,
            ArtifactOwnershipClassification.Serialization,
            ["profile"],
            SerializationOwners,
            "The serialization owner governs an exact immutable JSON profile."),
        Rule(
            SupportedArtifactKind.JsonSerializationContribution,
            ArtifactOwnershipClassification.Serialization,
            ["contribution"],
            SerializationOwners,
            "The contributing domain or package owns typed JSON contribution behavior."),
        Rule(
            SupportedArtifactKind.CanonicalJsonValue,
            ArtifactOwnershipClassification.Serialization,
            ["canonical-json-value"],
            SerializationOwners,
            "The serialization owner governs opaque canonical bytes at an approved untyped boundary."),
        Rule(
            SupportedArtifactKind.TaskDefinition,
            ArtifactOwnershipClassification.Tasking,
            ["task-definition"],
            DomainOwners,
            "The consumer domain owns requested-work meaning."),
        Rule(
            SupportedArtifactKind.TaskScheduleDescriptor,
            ArtifactOwnershipClassification.Tasking,
            ["task-schedule"],
            DomainOwners,
            "The consumer domain owns versioned trigger intent."),
        Rule(
            SupportedArtifactKind.HostComposition,
            ArtifactOwnershipClassification.HostComposition,
            ["host"],
            HostOwners,
            "The host owns its exact selected composition."),
        Rule(
            SupportedArtifactKind.LocalPublishManifest,
            ArtifactOwnershipClassification.GeneratedProjection,
            ["manifest"],
            HostOwners,
            "The published host owns the deterministic local-publish manifest."),
        Rule(
            SupportedArtifactKind.GeneratedHealthConfiguration,
            ArtifactOwnershipClassification.HostComposition,
            ["configuration"],
            HostOwners,
            "The host owns explicit generated health configuration."),
    ];

    /// <summary>Gets all rules in <see cref="SupportedArtifactKind"/> declaration order.</summary>
    public static ImmutableArray<SupportedArtifactKindOwnership> All => Rules;

    /// <summary>Resolves the canonical ownership rule for a supported kind.</summary>
    /// <exception cref="ArgumentOutOfRangeException">The value is not a supported enum member.</exception>
    public static SupportedArtifactKindOwnership Resolve(SupportedArtifactKind artifactKind)
    {
        var ordinal = (int)artifactKind;
        if (ordinal < 0 ||
            ordinal >= Rules.Length ||
            Rules[ordinal].ArtifactKind != artifactKind)
        {
            throw new ArgumentOutOfRangeException(
                nameof(artifactKind),
                artifactKind,
                "The artifact kind has no canonical ownership rule.");
        }

        return Rules[ordinal];
    }

    /// <summary>Returns whether an artifact identity kind is valid for the supported kind.</summary>
    public static bool SupportsArtifactIdentity(
        SupportedArtifactKind artifactKind,
        string identityKind) =>
        Resolve(artifactKind).ArtifactIdentityKinds.Contains(
            identityKind,
            StringComparer.Ordinal);

    /// <summary>Returns whether an owner identity kind is valid for the supported kind.</summary>
    public static bool SupportsOwnerIdentity(
        SupportedArtifactKind artifactKind,
        string ownerKind) =>
        Resolve(artifactKind).OwnerIdentityKinds.Contains(
            ownerKind,
            StringComparer.Ordinal);

    private static SupportedArtifactKindOwnership Rule(
        SupportedArtifactKind artifactKind,
        ArtifactOwnershipClassification classification,
        ImmutableArray<string> artifactIdentityKinds,
        ImmutableArray<string> ownerIdentityKinds,
        string canonicalOwnership) =>
        new(
            artifactKind,
            classification,
            artifactIdentityKinds,
            ownerIdentityKinds,
            canonicalOwnership);
}
