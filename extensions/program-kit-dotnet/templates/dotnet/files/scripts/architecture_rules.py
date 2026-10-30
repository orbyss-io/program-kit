RUNTIME_PROJECT_ROLES = {"core", "helper", "implementation", "provider", "bridge", "test"}
ACTIVATABLE_PROJECT_ROLES = {"implementation", "provider", "bridge"}
CAPABILITY_IMPLEMENTATION_ROLES = {"implementation", "provider", "bridge"}
ALLOWED_ROLE_REFERENCES = {
    "core": {"core"},
    "helper": {"core", "helper"},
    "implementation": {"core", "helper"},
    "provider": {"core", "helper"},
    "bridge": {"core", "helper"},
    "test": RUNTIME_PROJECT_ROLES,
}


def validate_project_role(role, path):
    """Diagnose retained presets without relabeling or changing consumer source."""
    if role == "composition":
        raise ValueError(
            "PKA022 retired C# composition project role: " + path
            + "; move feature selection to shell/deployment configuration and service/lifecycle "
            "registration to its owning feature. Review actual responsibilities before explicitly "
            "repairing or removing the project; do not merely relabel it. Consumer source is unchanged."
        )
    if not isinstance(role, str) or role not in RUNTIME_PROJECT_ROLES:
        raise ValueError("Unknown architecture role: " + path + "; " + str(role))


LEGACY_PROJECT_MARKERS = {"feature", "domain", "contracts", "application", "infrastructure"}
FORBIDDEN_CORE_PACKAGE_PREFIXES = (
    "cshells",
    "nuplane",
    "microsoft.aspnetcore",
    "microsoft.entityframeworkcore",
    "microsoft.extensions.dependencyinjection",
    "newtonsoft.json",
    "npgsql",
    "microsoft.data.sqlclient",
    "microsoft.data.sqlite",
    "system.text.json",
)
PERSISTENCE_PACKAGE_PREFIXES = (
    "microsoft.entityframeworkcore", "npgsql", "microsoft.data.sqlclient", "microsoft.data.sqlite",
)
