from __future__ import annotations

import sys
from pathlib import Path

from specify_cli.extensions import ExtensionManifest
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    extension_path = root / "extensions" / "program-kit-governance" / "extension.yml"
    workflow_path = root / "workflows" / "program-kit-bootstrap" / "workflow.yml"

    ExtensionManifest(extension_path)
    workflow = WorkflowDefinition.from_yaml(workflow_path)
    errors = validate_workflow(workflow)
    if errors:
        for error in errors:
            print(f"workflow error: {error}", file=sys.stderr)
        return 1

    print("Extension and workflow manifests are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
