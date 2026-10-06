RUNTIME_PROJECT_ROLES = {"core", "helper", "implementation", "provider", "bridge", "composition", "test"}
ACTIVATABLE_PROJECT_ROLES = {"implementation", "provider", "bridge", "composition"}
CAPABILITY_IMPLEMENTATION_ROLES = {"implementation", "provider", "bridge"}
ALLOWED_ROLE_REFERENCES = {
    "core": {"core"},
    "helper": {"core", "helper"},
    "implementation": {"core", "helper"},
    "provider": {"core", "helper"},
    "bridge": {"core", "helper"},
    "composition": {"core", "helper", "implementation", "provider", "bridge", "composition"},
    "test": RUNTIME_PROJECT_ROLES,
}
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
