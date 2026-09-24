"""Executable bootstrap stage declarations; contexts and native recovery consume this authority."""
from __future__ import annotations

STAGES = {
    'assessment': {'requires': ['confirmed-intent'], 'resolves': ['first-slice', 'defaults', 'capability-dependencies'], 'later': ['feature-design', 'production-operations'], 'next_owner': 'research', 'restart': 'prepare-assessment-context'},
    'research': {'requires': ['first-slice', 'defaults'], 'resolves': ['provider-findings-or-owned-unknowns', 'source-evidence', 'applicable-managed-pins'], 'later': ['feature-behavior'], 'next_owner': 'architecture', 'restart': 'prepare-research-context'},
    'architecture': {'requires': ['provider-findings-or-owned-unknowns', 'applicable-managed-pins'], 'resolves': ['composition', 'ownership', 'architecture-risks'], 'later': ['feature-types', 'future-journey-details'], 'next_owner': 'tooling', 'restart': 'prepare-architecture-context'},
    'tooling': {'requires': ['composition', 'ownership'], 'resolves': ['enforcement-tools', 'verification-due-phases'], 'later': ['application-scaffolding'], 'next_owner': 'roadmap', 'restart': 'prepare-tooling-context'},
    'roadmap': {'requires': ['first-slice', 'architecture-risks'], 'resolves': ['first-entry', 'future-portfolio'], 'later': ['future-specifications'], 'next_owner': 'closure', 'restart': 'prepare-roadmap-context'},
    'closure': {'requires': ['candidate-entries', 'provider-findings-or-owned-unknowns'], 'resolves': ['first-slice-design-review', 'executable-proof-plan', 'owned-deferrals'], 'later': ['feature-behavior', 'production-approval'], 'next_owner': 'execute-compatibility-proofs', 'restart': 'prepare-closure-context'},
    'readiness': {'requires': ['reviewed-baseline', 'owned-open-obligations'], 'resolves': ['initialized-baseline-and-phase-eligibility'], 'later': ['ready-to-code', 'ready-to-deliver'], 'next_owner': 'specification-intake', 'restart': 'prepare-readiness-context'},
}

STAGE_ARTIFACTS: dict[str, tuple[str, ...]] = {
    "assessment": (),
    "research": (
        "docs/architecture/bootstrap-assessment.md",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
    ),
    "architecture": (
        ".specify/memory/constitution.md",
        ".specify/memory/constitution-ratification.json",
        ".specify/governance/bootstrap-assessment-approval.json",
        "docs/architecture/bootstrap-assessment.md",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
        "docs/architecture/tooling-evaluation.md",
    ),
    "tooling": (
        ".specify/memory/constitution.md",
        ".specify/memory/constitution-ratification.json",
        ".specify/governance/bootstrap-assessment-approval.json",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
        "docs/architecture/tooling-evaluation.md",
        "docs/architecture/architecture.md",
        "docs/architecture/quality-attributes.md",
        "docs/architecture/technology-radar.md",
        "docs/architecture/traceability.md",
        "docs/architecture/decisions/bootstrap-baseline.md",
    ),
    "roadmap": (
        ".specify/memory/constitution.md",
        ".specify/memory/constitution-ratification.json",
        ".specify/governance/bootstrap-assessment-approval.json",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
        "docs/architecture/tooling-evaluation.md",
        "docs/architecture/architecture.md",
        "docs/architecture/quality-attributes.md",
        "docs/architecture/quality-system.md",
        "docs/architecture/technology-radar.md",
        "docs/architecture/traceability.md",
        "docs/architecture/decisions/bootstrap-baseline.md",
    ),
    "readiness": (
        ".specify/memory/constitution.md",
        ".specify/memory/constitution-ratification.json",
        ".specify/governance/bootstrap-assessment-approval.json",
        ".specify/governance/bootstrap-approval.json",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
        "docs/architecture/tooling-evaluation.md",
        "docs/architecture/architecture.md",
        "docs/architecture/quality-attributes.md",
        "docs/architecture/quality-system.md",
        "docs/architecture/specification-roadmap.md",
        "docs/architecture/technology-radar.md",
        "docs/architecture/traceability.md",
        "docs/architecture/decisions/bootstrap-baseline.md",
    ),
}


STAGE_FULL_READS = {
    "assessment": (),
    "research": ("docs/architecture/bootstrap-decisions.json",),
    "architecture": (
        ".specify/memory/constitution.md",
        "docs/architecture/architecture-map.json",
    ),
    "tooling": (".specify/memory/constitution.md",),
    "roadmap": (".specify/memory/constitution.md",),
    "readiness": (".specify/memory/constitution.md",),
}


STAGE_FOCUS = {
    "assessment": "Project confirmed intake into a proportional decision baseline without reopening accepted choices.",
    "research": "Verify only selected technologies and capabilities; excluded surfaces are out of scope.",
    "architecture": "Define the smallest governed architecture that realizes the confirmed intake journeys.",
    "tooling": "Adopt only controls required by selected capabilities and accepted boundaries.",
    "roadmap": "Create outcome-oriented specification entries from confirmed journeys and accepted decisions.",
    "readiness": "Validate baseline initialization and report each slice's phase eligibility and owned open work.",
}


INTAKE_STAGE_FIELDS = {
    "assessment": (
        "facts", "scope", "actors", "journeys", "quality_requirements", "integrations",
        "choices", "capability_assessments", "domain_analysis", "open_items",
        "candidate_slice_signals", "routing",
    ),
    "research": (
        "quality_requirements", "choices", "capability_assessments", "open_items", "routing",
    ),
    "architecture": (
        "facts", "scope", "actors", "journeys", "quality_requirements", "integrations", "choices",
        "domain_analysis", "open_items", "candidate_slice_signals", "routing",
    ),
    "tooling": (
        "scope", "quality_requirements", "open_items", "routing",
    ),
    "roadmap": (
        "scope", "actors", "journeys", "open_items", "candidate_slice_signals", "domain_analysis", "quality_requirements",
    ),
    "readiness": (
        "actors", "journeys", "open_items", "candidate_slice_signals", "domain_analysis", "quality_requirements",
    ),
}


MAP_STAGE_FIELDS = {
    "assessment": ("constraints", "elements", "relationships", "views"),
    "research": ("constraints", "elements", "relationships", "views"),
    # Architecture edits the canonical seed, so a second lossy copy in the brief is actively
    # harmful. The seed is a required full read and this projection carries only its identity.
    "architecture": (),
    "tooling": ("decisions", "constraints", "elements", "relationships"),
    # Roadmap needs owned outcomes/contracts, not a duplicate of diagram layout.
    "roadmap": ("decisions", "constraints", "elements", "relationships", "strategic_model"),
    "readiness": ("decisions", "constraints", "elements", "relationships", "views", "strategic_model"),
}


STAGE_RECORD_FIELDS = {
    "tooling": {
        "decisions": ("id", "title", "status", "scope"),
        "constraints": ("id", "statement", "status", "applies_to", "decision_refs"),
        "elements": ("id", "type", "name", "description", "properties", "status", "ownership", "parent", "decision_refs"),
        "relationships": ("id", "source", "target", "status", "decision_refs"),
    },
    "roadmap": {
        "decisions": ("id", "title", "status", "scope"),
        "constraints": ("id", "statement", "status", "applies_to", "decision_refs"),
        "elements": ("id", "type", "name", "properties", "status", "ownership", "parent", "decision_refs"),
        "relationships": ("id", "source", "target", "status", "decision_refs"),
        "views": ("key", "type", "title", "scope", "elements", "relationships", "decision_refs"),
    },
    "readiness": {
        "decisions": ("id", "path", "title", "status", "scope", "supersedes"),
        "constraints": ("id", "statement", "status", "applies_to", "decision_refs"),
        "elements": ("id", "type", "name", "properties", "status", "ownership", "parent", "decision_refs"),
        "relationships": ("id", "source", "target", "status", "decision_refs"),
        "views": ("key", "type", "title", "scope", "elements", "relationships", "decision_refs"),
    },
}


OUTPUT_CONTRACTS = {
    "assessment": {
        "write_paths": [
            "docs/architecture/bootstrap-assessment.md",
            "docs/architecture/decision-backlog.md",
            "docs/architecture/bootstrap-decisions.json",
        ],
        "contract_references": [
            ".specify/extensions/program-kit-governance/references/bootstrap-decisions.schema.json"
        ],
    },
    "research": {
        "write_paths": [
            "docs/architecture/tooling-evaluation.md",
            "docs/architecture/bootstrap-decisions.json",
        ],
        "contract_references": [
            ".specify/extensions/program-kit-governance/references/bootstrap-decisions.schema.json"
        ],
    },
    "architecture": {
        "write_paths": [
            "docs/architecture/README.md",
            "docs/architecture/architecture.md",
            "docs/architecture/quality-attributes.md",
            "docs/architecture/technology-radar.md",
            "docs/architecture/traceability.md",
            "docs/architecture/bootstrap-prerequisites.json",
            "docs/architecture/architecture-map.json",
            "docs/architecture/building-block-selection.json",
            "docs/architecture/workspace.dsl",
            "docs/architecture/decisions/README.md",
            "docs/architecture/decisions/bootstrap-baseline.md",
        ],
        "contract_references": [
            ".specify/extensions/program-kit-governance/references/architecture-map.schema.json",
            ".specify/extensions/program-kit-governance/references/bootstrap-lifecycle.md",
            ".specify/extensions/program-kit-building-blocks/references/building-block-selection.schema.json",
        ],
    },
    "tooling": {
        "write_paths": ["docs/architecture/quality-system.md"],
        "contract_references": [],
    },
    "roadmap": {
        "write_paths": [
            "docs/architecture/specification-roadmap.md",
            "docs/architecture/bootstrap-prerequisites.json",
            "docs/architecture/architecture.md",
            "docs/architecture/traceability.md",
        ],
        "contract_references": [".specify/extensions/program-kit-governance/references/bootstrap-lifecycle.md"],
    },
    "readiness": {
        "write_paths": ["docs/architecture/readiness-report.md"],
        "contract_references": [".specify/extensions/program-kit-governance/references/bootstrap-lifecycle.md"],
    },
}


STAGE_STARTS = {
    'validate-assessment-output': 'prepare-assessment-context',
    'validate-assessment': 'prepare-assessment-context',
    'write-assessment-review': 'prepare-assessment-context',
    'accept-assessment': 'prepare-assessment-context',
    'assessment': 'prepare-assessment-context',
    'research': 'prepare-research-context',
    'validate-research-output': 'prepare-research-context',
    'constitution-draft': 'constitution-draft',
    'validate-constitution-draft': 'constitution-draft',
    'write-constitution-review': 'constitution-draft',
    'ratify-constitution': 'constitution-draft',
    'architecture-dispatch': 'prepare-architecture-context',
    'validate-architecture-output': 'prepare-architecture-context',
    'validate-architecture-alignment': 'prepare-architecture-context',
    'write-bootstrap-review': 'prepare-architecture-context',
    'accept-bootstrap': 'write-bootstrap-review',
    'auto-accept-bootstrap': 'write-bootstrap-review',
    'tooling': 'prepare-tooling-context',
    'validate-tooling-output': 'prepare-tooling-context',
    'specification-roadmap': 'prepare-roadmap-context',
    'validate-roadmap-output': 'prepare-roadmap-context',
    'architecture-prerequisite-closure': 'architecture-prerequisite-closure',
    'execute-compatibility-proofs': 'execute-compatibility-proofs',
    'validate-prerequisite-closure': 'architecture-prerequisite-closure',
    'recovery-closure': 'verify-recovery-source',
    'recovery-synchronize': 'verify-recovery-source',
    'recovery-review': 'verify-recovery-source',
    'recovery-accept': 'verify-recovery-source',
    'prepare-recovery-readiness': 'prepare-recovery-readiness',
    'recovery-readiness': 'prepare-recovery-readiness',
    'recovery-evaluate': 'prepare-recovery-readiness',
    'recovery-require-ready': 'verify-recovery-source',
}



STAGE_ARTIFACTS['closure'] = (
    '.specify/memory/constitution.md',
    'docs/architecture/bootstrap-decisions.json',
    'docs/architecture/bootstrap-prerequisites.json',
    'docs/architecture/specification-roadmap.md',
    'docs/architecture/tooling-evaluation.md',
    'docs/architecture/architecture.md',
    'docs/architecture/quality-attributes.md',
    'docs/architecture/quality-system.md',
    'docs/architecture/traceability.md',
)
STAGE_FULL_READS['closure'] = ('.specify/memory/constitution.md', 'docs/architecture/bootstrap-prerequisites.json')
STAGE_FOCUS['closure'] = 'Review the first-slice design against confirmed outcomes and owned verification before approval; resolve substantive findings through existing questions and prerequisites, and select maintained compatibility checks.'
INTAKE_STAGE_FIELDS['closure'] = ('actors', 'journeys', 'quality_requirements', 'candidate_slice_signals', 'open_items', 'routing')
# The first-feature handoff identifies the exact slice scope. Deeper design and
# quality sources are indexed above rather than duplicating the whole portfolio.
MAP_STAGE_FIELDS['closure'] = ('decisions',)
STAGE_RECORD_FIELDS['closure'] = {'decisions': ('id', 'path', 'title', 'status', 'scope')}
OUTPUT_CONTRACTS['closure'] = {
    'write_paths': ['docs/architecture/bootstrap-prerequisites.json', 'docs/architecture/bootstrap-proof-plan.json', 'docs/architecture/bootstrap-acceptance-scope.json', 'docs/architecture/specification-roadmap.md'],
    'contract_references': ['.specify/extensions/program-kit-governance/references/bootstrap-lifecycle.md', '.specify/extensions/program-kit-governance/references/bootstrap-proof-plan.schema.json'],
}
STAGE_STARTS.update({
    'require-first-feature-handoff': 'prepare-closure-context',
    'architecture-prerequisite-closure': 'prepare-closure-context',
    'validate-closure-output': 'prepare-closure-context',
    'validate-prerequisite-closure': 'prepare-closure-context',
    'resolve-assessment-defaults': 'prepare-assessment-context',
    'resolve-research-defaults': 'prepare-research-context',
})
for _stage in STAGES:
    STAGE_STARTS['require-' + _stage + '-handoff'] = 'require-' + _stage + '-handoff'
    STAGE_STARTS['require-' + _stage + '-answers'] = STAGES[_stage]['restart']
