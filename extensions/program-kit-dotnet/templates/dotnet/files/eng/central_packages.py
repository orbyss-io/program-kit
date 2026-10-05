"""Strict, shared literal central-package import authority."""
from pathlib import Path
import re
from xml.etree import ElementTree


def central_package_versions(repository: Path) -> dict[str, str]:
    """Read the supported literal CPM import graph, without guessing MSBuild evaluation."""
    repository = repository.resolve()
    central = (repository / "Directory.Packages.props").resolve()
    versions: dict[str, str] = {}
    origins: dict[str, Path] = {}
    visited: set[Path] = set()
    active: set[Path] = set()

    def fail(path: Path, detail: str) -> None:
        raise ValueError(f"PKR019 unsupported central package pins in '{path}': {detail}")

    def local_path(owner: Path, value: str) -> Path:
        if not value or re.search(r"[$@%*?;:]", value) or value.startswith(("/", "\\")):
            fail(owner, "imports must use literal repository-relative paths")
        result = (owner.parent / value.replace("\\", "/")).resolve()
        if not result.is_relative_to(repository):
            fail(owner, "import escapes the repository")
        return result

    def visit(path: Path) -> None:
        if not path.is_relative_to(repository):
            fail(path, "props file escapes the repository")
        if path in active:
            fail(path, "cyclic import")
        if path in visited:
            return  # MSBuild also ignores repeated imports of the same project.
        try:
            root = ElementTree.parse(path).getroot()
        except (OSError, ElementTree.ParseError) as error:
            fail(path, f"cannot read required props file: {error}")
        active.add(path)
        if root.tag.rsplit("}", 1)[-1] != "Project" or root.attrib:
            fail(path, "expected a plain Project without SDK or evaluation attributes")
        for group in root:
            tag = group.tag.rsplit("}", 1)[-1]
            if tag == "Import":
                if set(group.attrib) - {"Project", "Condition"} or len(group):
                    fail(path, "unsupported Import attributes or content")
                imported = local_path(path, group.get("Project", ""))
                condition = group.get("Condition")
                if condition is not None:
                    exists = re.fullmatch(r"\s*Exists\(\s*(['\"])([^'\"]+)\1\s*\)\s*", condition, re.IGNORECASE)
                    # Only the root-file Exists(import path) contract is context-independent.
                    if path != central or not exists or local_path(path, exists[2]) != imported:
                        fail(path, "only root-level Exists of the literal import path is supported")
                    if not imported.exists():
                        continue
                visit(imported)
            elif tag == "PropertyGroup":
                if set(group.attrib) - {"Label"}:
                    fail(path, "conditional property groups require MSBuild evaluation")
                for prop in group:
                    if prop.attrib or len(prop):
                        fail(path, "conditional or structured properties require MSBuild evaluation")
                    if prop.tag.rsplit("}", 1)[-1] == "ManagePackageVersionsCentrally" and (prop.text or "").strip().lower() != "true":
                        fail(path, "central package management must remain enabled")
            elif tag == "ItemGroup":
                if set(group.attrib) - {"Label"}:
                    fail(path, "conditional item groups require MSBuild evaluation")
                for item in group:
                    if item.tag.rsplit("}", 1)[-1] != "PackageVersion" or set(item.attrib) - {"Include", "Version"}:
                        fail(path, "only unconditional PackageVersion Include items are supported; Update/Remove are not evaluated")
                    identity = item.get("Include", "")
                    version = item.get("Version")
                    if len(item):
                        if (version is not None or len(item) != 1 or item[0].tag.rsplit("}", 1)[-1] != "Version"
                                or item[0].attrib or len(item[0])):
                            fail(path, "ambiguous or conditional Version metadata")
                        version = (item[0].text or "").strip()
                    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", identity):
                        fail(path, "package IDs must be single literal identities")
                    if not version or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){2,3}(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?", version):
                        fail(path, f"'{identity}' requires an exact literal version, without ranges, floating pins or properties")
                    key = identity.casefold()
                    if key in versions:
                        fail(path, f"duplicate/conflicting pin for '{identity}' (already declared in '{origins[key]}')")
                    versions[key], origins[key] = version, path
            else:
                fail(path, f"'{tag}' requires unsupported MSBuild evaluation")
        active.remove(path)
        visited.add(path)

    visit(central)
    return versions
