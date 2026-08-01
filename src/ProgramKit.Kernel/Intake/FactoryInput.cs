using System;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Kernel.Intake;

public sealed record FactoryInput(
    FactoryOperation Operation,
    ConstructionMode? ConstructionMode,
    RequestedEffect RequestedEffect,
    string WorkspaceIdentity,
    DateTimeOffset EvaluationInstant,
    string EvaluationSource,
    bool AuthorityApproved,
    DateTimeOffset AuthorityNotBefore,
    DateTimeOffset AuthorityNotAfter,
    string ProviderSelection,
    string ProfileSelection,
    JsonObject Definition,
    JsonObject CanonicalDocument);
