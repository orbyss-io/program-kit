# Orbyss.ProgramKit.DevContainers

This package generates deterministic `.devcontainer` artifacts from explicit,
typed development-container input. It supports a bounded image, Dockerfile, or
single-primary-service Compose profile; exact-version features; structured
mounts and forwarded ports; non-root users; exact lifecycle commands; and
opaque digest-bound scripts.

The generator returns files and a tree digest. It never writes those files,
resolves images or features, executes lifecycle commands, starts containers, or
claims that a Dev Container is a governed work boundary. Script and Dockerfile
meaning remains owned by the human input.

The package includes the exact official Dev Container base schema selected by
the Program Kit profile. Its schema module can be used with the Program Kit
Workbench validator when a consumer needs independent JSON-schema validation.
