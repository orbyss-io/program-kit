"""Create only the Phase 0 resources explicitly approved in the decision record.

Run from the repository root with ``python -m scripts.delivery_phase0.setup``.
An ambiguous setup attempt stops for inspection; this script never recreates it.
No cleanup operation is provided. No coding agents or pipelines are started.
"""
from __future__ import annotations

import json
from pathlib import Path
import time
import uuid

from .transport import ApiError, Transport

ROOT = Path(__file__).resolve().parents[2]
JOURNAL = ROOT / "artifacts/delivery-phase0/resources.json"
AZURE_PROJECT = "ProgramKit.Delivery.Phase0"
GH_OWNER = "orbyss-io"
GH_REPO = "program-kit-delivery-phase0"
GH_PROJECT = "Program Kit Delivery Phase 0"


def save(data):
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    staged = JOURNAL.with_suffix(".tmp")
    staged.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    staged.replace(JOURNAL)


def create_once(journal, key, action):
    previous = journal["resources"].get(key)
    if previous:
        if previous["state"] != "confirmed":
            raise RuntimeError(f"Inspect uncertain setup attempt {key}; do not recreate it")
        return previous["value"]
    journal["resources"][key] = {"state": "dispatched"}
    save(journal)
    value = action()
    journal["resources"][key] = {"state": "confirmed", "value": value}
    save(journal)
    print(f"Confirmed setup: {key}", flush=True)
    return value


def main():
    journal = json.loads(JOURNAL.read_text()) if JOURNAL.exists() else {
        "version": 1, "setup_id": str(uuid.uuid4()), "resources": {},
    }
    marker = "Program Kit disposable Phase 0; setup=" + journal["setup_id"]
    az, gh = Transport("azure"), Transport("github")
    if "azure_project_request" not in journal["resources"]:
        projects = az.request("GET", "/_apis/projects?$top=1000")["value"]
        if any(p["name"].lower() == AZURE_PROJECT.lower() for p in projects):
            raise RuntimeError("Azure probe name already exists without this setup journal")
    processes = az.request("GET", "/_apis/process/processes")["value"]
    agile = next(p["id"] for p in processes if p["name"] == "Agile" and p["type"] == "system")
    operation = create_once(journal, "azure_project_request", lambda: az.request("POST", "/_apis/projects", {
        "name": AZURE_PROJECT, "description": marker, "visibility": "private",
        "capabilities": {"versioncontrol": {"sourceControlType": "Git"},
                         "processTemplate": {"templateTypeId": agile}},
    }))
    for _ in range(30):
        status = az.request("GET", "/_apis/operations/" + operation["id"])
        if status["status"] == "succeeded":
            break
        if status["status"] in ("failed", "cancelled"):
            raise RuntimeError("Azure project creation did not succeed")
        time.sleep(2)
    else:
        raise RuntimeError("Project setup still pending; rerun to observe the recorded operation")
    project = az.request("GET", "/_apis/projects/" + AZURE_PROJECT)
    if project.get("description") != marker or project.get("visibility") != "private":
        raise RuntimeError("Azure project attribution/privacy check failed")
    journal["azure_project_id"] = project["id"]
    save(journal)
    repo = create_once(journal, "azure_repo", lambda: az.request("POST", "/" + project["id"] + "/_apis/git/repositories", {
        "name": "delivery-coordination", "project": {"id": project["id"]},
    }))
    if repo["project"]["id"] != project["id"]:
        raise RuntimeError("Azure repository outside approved scope")

    if "github_repo" not in journal["resources"]:
        try:
            gh.request("GET", f"/repos/{GH_OWNER}/{GH_REPO}")
        except ApiError as error:
            if error.status != 404:
                raise
        else:
            raise RuntimeError("GitHub probe name already exists without this setup journal")
    repository = create_once(journal, "github_repo", lambda: gh.request("POST", f"/orgs/{GH_OWNER}/repos", {
        "name": GH_REPO, "description": marker, "private": True, "auto_init": True,
        "has_issues": True, "has_wiki": False,
    }))
    current = gh.request("GET", f"/repos/{GH_OWNER}/{GH_REPO}")
    if current["id"] != repository["id"] or current["description"] != marker or not current["private"]:
        raise RuntimeError("GitHub repository attribution/privacy check failed")
    organization = gh.graphql("query($login:String!){organization(login:$login){id projectsV2(first:100){nodes{id title} pageInfo{hasNextPage}}}}", {"login": GH_OWNER})["organization"]
    if "github_project" not in journal["resources"]:
        if organization["projectsV2"]["pageInfo"]["hasNextPage"]:
            raise RuntimeError("Incomplete project discovery; cannot verify setup name")
        if any(p["title"] == GH_PROJECT for p in organization["projectsV2"]["nodes"]):
            raise RuntimeError("GitHub Project name already exists without this setup journal")
    board = create_once(journal, "github_project", lambda: gh.graphql(
        "mutation($owner:ID!,$title:String!){createProjectV2(input:{ownerId:$owner,title:$title}){projectV2{id number url public}}}",
        {"owner": organization["id"], "title": GH_PROJECT})["createProjectV2"]["projectV2"])
    create_once(journal, "github_project_metadata", lambda: gh.graphql(
        "mutation($id:ID!,$description:String!){updateProjectV2(input:{projectId:$id,public:false,shortDescription:$description}){projectV2{id public shortDescription}}}",
        {"id": board["id"], "description": marker})["updateProjectV2"]["projectV2"])
    journal["setup_complete"] = True
    save(journal)
    print("Disposable setup complete; setup does not run probes.")


if __name__ == "__main__":
    main()
