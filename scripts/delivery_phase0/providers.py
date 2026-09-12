"""Minimal provider primitives for the approved Phase 0 scopes only."""
from __future__ import annotations

import base64
import json
from urllib.parse import quote

from .setup import AZURE_PROJECT, GH_OWNER, GH_REPO, JOURNAL, create_once
from .transport import ApiError, Transport

BRANCH = "coordination"
STATE_PATH = "state.json"


class Store:
    def __init__(self, provider):
        self.provider = provider
        self.api = Transport(provider)
        journal = json.loads(JOURNAL.read_text())
        self.journal = journal
        marker = "Program Kit disposable Phase 0; setup=" + journal["setup_id"]
        if provider == "azure":
            self.project = journal["azure_project_id"]
            self.repo = journal["resources"]["azure_repo"]["value"]["id"]
            self.prefix = f"/{self.project}/_apis/git/repositories/{self.repo}"
            project = self.api.request("GET", "/_apis/projects/" + self.project)
            repo = self.api.request("GET", self.prefix)
            if project["name"] != AZURE_PROJECT or project.get("description") != marker or project["visibility"] != "private" or repo["project"]["id"] != self.project or repo["name"] != "delivery-coordination":
                raise RuntimeError("Azure scope attribution failed")
        else:
            self.prefix = f"/repos/{GH_OWNER}/{GH_REPO}"
            repo = self.api.request("GET", self.prefix)
            expected = journal["resources"]["github_repo"]["value"]["id"]
            if repo["id"] != expected or not repo["private"] or repo["description"] != marker:
                raise RuntimeError("GitHub scope attribution failed")
            self.repo = repo["node_id"]

    def initialize(self):
        state = {"schemaVersion": 1, "space": self.journal["setup_id"], "claims": {}, "operations": {}}
        if self.provider == "azure":
            create_once(self.journal, "azure_initial_state", lambda: self.commit("0" * 40, state, initial=True))
        else:
            repo = self.api.request("GET", self.prefix)
            ref = self.api.request("GET", self.prefix + "/git/ref/heads/" + quote(repo["default_branch"]))
            create_once(self.journal, "github_branch", lambda: self.api.request("POST", self.prefix + "/git/refs", {
                "ref": "refs/heads/" + BRANCH, "sha": ref["object"]["sha"],
            }))
            create_once(self.journal, "github_initial_state", lambda: self.commit(self.head(), state))

    def head(self):
        if self.provider == "azure":
            refs = self.api.request("GET", self.prefix + "/refs?filter=heads/" + BRANCH)["value"]
            return next(r["objectId"] for r in refs if r["name"] == "refs/heads/" + BRANCH)
        # Read the reference through the same GraphQL service used for the CAS.
        # REST ref reads proved capable of briefly returning a previous head.
        value = self.api.graphql("query($owner:String!,$name:String!,$ref:String!){repository(owner:$owner,name:$name){ref(qualifiedName:$ref){target{oid}}}}",
            {"owner": GH_OWNER, "name": GH_REPO, "ref": "refs/heads/" + BRANCH})
        return value["repository"]["ref"]["target"]["oid"]

    def read(self, head=None):
        if head is None:
            head = self.head()
            acknowledged = getattr(self, "_acknowledged_head", None)
            if self.provider == "github" and acknowledged and head != acknowledged:
                comparison = self.api.request("GET", self.prefix + "/compare/" + acknowledged + "..." + head)
                if comparison["status"] == "behind":
                    # A lagging ref read cannot erase this client's acknowledged write.
                    head = acknowledged
                elif comparison["status"] not in ("ahead", "identical"):
                    raise RuntimeError("Coordinator history diverged; reconcile before writing")
        if self.provider == "azure":
            item = self.api.request("GET", self.prefix + "/items?path=/" + STATE_PATH + "&includeContent=true&versionDescriptor.versionType=commit&versionDescriptor.version=" + head)
            state = json.loads(item["content"])
        else:
            item = self.api.request("GET", self.prefix + "/contents/" + STATE_PATH + "?ref=" + head)
            state = json.loads(base64.b64decode(item["content"]))
        if state["space"] != self.journal["setup_id"]:
            raise RuntimeError("Coordination state belongs to another space")
        return head, state

    def commit(self, expected, state, initial=False):
        text = json.dumps(state, sort_keys=True, indent=2) + "\n"
        if self.provider == "azure":
            result = self.api.request("POST", self.prefix + "/pushes", {
                "refUpdates": [{"name": "refs/heads/" + BRANCH, "oldObjectId": expected}],
                "commits": [{"comment": "Phase 0 conditional coordination update", "changes": [{
                    "changeType": "add" if initial else "edit", "item": {"path": "/" + STATE_PATH},
                    "newContent": {"content": text, "contentType": "rawtext"},
                }]}],
            })
            self._acknowledged_head = result["commits"][0]["commitId"]
            return self._acknowledged_head
        result = self.api.graphql("""mutation($input:CreateCommitOnBranchInput!){
            createCommitOnBranch(input:$input){commit{oid}}} """, {"input": {
            "branch": {"repositoryNameWithOwner": GH_OWNER + "/" + GH_REPO, "branchName": BRANCH},
            "expectedHeadOid": expected, "message": {"headline": "Phase 0 conditional coordination update"},
            "fileChanges": {"additions": [{"path": STATE_PATH, "contents": base64.b64encode(text.encode()).decode()}]},
        }})
        self._acknowledged_head = result["createCommitOnBranch"]["commit"]["oid"]
        return self._acknowledged_head

    def is_stale(self, error):
        if self.provider == "azure":
            return error.status in (400, 409) and any("Stale" in code or "ReferenceUpdate" in code for code in error.codes)
        return error.status == 200 and "STALE_DATA" in error.codes

    def work_path(self, native_id=None, kind=None):
        if self.provider == "azure":
            return f"/{self.project}/_apis/wit/workitems/" + (str(native_id) if native_id else "$" + quote(kind))
        return self.prefix + "/issues" + ("/" + str(native_id) if native_id else "")

    def create_item(self, title, body, kind="User Story"):
        if self.provider == "azure":
            return self.api.request("POST", self.work_path(kind=kind), [
                {"op": "add", "path": "/fields/System.Title", "value": title},
                {"op": "add", "path": "/fields/System.Description", "value": body},
            ], "application/json-patch+json")
        return self.api.request("POST", self.work_path(), {"title": title, "body": body})

    def get_item(self, native_id):
        suffix = "?$expand=relations" if self.provider == "azure" else ""
        return self.api.request("GET", self.work_path(native_id) + suffix)

    def conditional_description(self, native_id, expected, body):
        if self.provider != "azure":
            raise NotImplementedError("GitHub shared text replacement requires a reviewed proposal")
        return self.api.request("PATCH", self.work_path(native_id), [
            {"op": "test", "path": "/rev", "value": expected},
            {"op": "add", "path": "/fields/System.Description", "value": body},
        ], "application/json-patch+json")


def item_id(provider, value):
    return value["id"] if provider == "azure" else value["number"]
