"""Explicit live API probes in the recorded disposable Phase 0 scopes.

Never imported by deterministic tests or CI. Run one provider at a time:
python -m scripts.delivery_phase0.probe azure|github
Evidence distinguishes live provider results from injected client interruption.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import time
import uuid

from .contract import Conflict, admit, checkpoint, dispatch, fingerprint, recover, release
from .providers import Store, item_id
from .setup import ROOT
from .transport import ApiError


class Probe:
    def __init__(self, provider):
        self.store = Store(provider)
        self.provider = provider
        self.run_id = str(uuid.uuid4())
        self.directory = ROOT / "artifacts/delivery-phase0/runs" / self.run_id
        self.directory.mkdir(parents=True)
        self.evidence = {"runId": self.run_id, "provider": provider, "startedAt": datetime.now(timezone.utc).isoformat(),
                         "cases": [], "createdItems": [], "complete": False,
                         "pythonVersion": sys.version.split()[0],
                         "sourceFiles": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in sorted((ROOT / "scripts/delivery_phase0").glob("*.py"))}}
        self.save()

    def save(self):
        target = self.directory / "evidence.json"
        staged = target.with_suffix(".tmp")
        staged.write_text(json.dumps(self.evidence, indent=2) + "\n", encoding="utf-8")
        staged.replace(target)

    def record(self, name, result, **details):
        self.evidence["cases"].append({"case": name, "result": result, **details})
        self.save()
        print(f"{self.provider}: {name}: {result}", flush=True)

    def races(self):
        for index in range(3):
            head, state = self.store.read()
            work = self.run_id + ":race:" + str(index)
            gate = self.directory / f"go-{index}"
            processes = []
            try:
                for contender in ("A", "B"):
                    ready = self.directory / f"ready-{index}-{contender}"
                    process = subprocess.Popen([sys.executable, "-m", "scripts.delivery_phase0.race_worker",
                        self.provider, head, work, contender, str(ready), str(gate)],
                        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    processes.append((process, ready))
                deadline = time.monotonic() + 60
                while not all(path.exists() for _, path in processes):
                    if time.monotonic() > deadline or any(p.poll() is not None for p, _ in processes):
                        raise RuntimeError("Race preparation failed")
                    time.sleep(0.1)
                gate.write_text("go")
                results = []
                for process, _ in processes:
                    stdout, stderr = process.communicate(timeout=60)
                    if process.returncode:
                        raise RuntimeError("Race worker failed before a classified result")
                    results.append(json.loads(stdout))
                self.record("conditional-claim-race-" + str(index), "observed", expectedHead=head, attempts=results)
                assert sum(r["outcome"] == "committed" for r in results) == 1
                assert sum(r["outcome"] == "rejected" for r in results) == 1
                current_head, current = self.store.read()
                winner = next(r for r in results if r["outcome"] == "committed")
                claim = current["claims"][work]
                assert claim["actor"]["executionId"] == winner["execution"]
                # Explicit takeover changes the generation; the obsolete worker must stop.
                changed = admit(current, work, {**claim["actor"], "executionId": "takeover"},
                                claim["basis"], claim["exclusiveResources"], takeover=True, authorized=True)
                self.store.commit(current_head, changed)
                try:
                    checkpoint(self.store.read()[1], work, claim["generation"], winner["execution"], claim["basis"])
                except Conflict:
                    self.record("obsolete-generation-" + str(index), "passed")
                else:
                    raise AssertionError("Old claim remained authorized")
                current_head, current = self.store.read()
                self.store.commit(current_head, release(current, work, claim["generation"] + 1, "takeover", claim["basis"]))
            finally:
                for process, _ in processes:
                    if process.poll() is None:
                        process.kill()
                    process.communicate()

    def create(self, label, kind="User Story", lose_response=False):
        operation_id = self.run_id + ":" + label
        title = "[Program Kit Phase 0] " + label
        description = "Synthetic delivery probe. Correlation: " + operation_id
        operation = {"id": operation_id, "destination": self.store.prefix,
                     "payloadFingerprint": fingerprint({"title": title, "description": description, "kind": kind}),
                     "state": "prepared"}
        head, state = self.store.read()
        assert operation_id not in state["operations"]
        state["operations"][operation_id] = operation
        self.store.commit(head, state)
        head, state = self.store.read()
        state["operations"][operation_id] = dispatch(operation)
        self.store.commit(head, state)
        # The operation is durably dispatched before the non-idempotent request.
        item = self.store.create_item(title, description, kind)
        native = item_id(self.provider, item)
        self.evidence["createdItems"].append(native)
        self.save()
        if lose_response:
            self.record("response-loss-injection", "injected", operationId=operation_id,
                        note="Provider succeeded; client deliberately omits identity persistence, then rereads remote items.")
            recovered = self.recover_created(operation_id, kind)
            assert recovered["state"] == "applied" and recovered["providerId"] == str(native)
        else:
            head, state = self.store.read()
            state["operations"][operation_id] = dict(operation, state="applied", providerId=str(native))
            self.store.commit(head, state)
        return native

    def recover_created(self, operation_id, kind="User Story"):
        for attempt in range(5):
            head, state = self.store.read()
            operation = state["operations"][operation_id]
            found, complete = self.find_marker(operation_id)
            matches = []
            for candidate in found:
                title = candidate["fields"]["System.Title"] if self.provider == "azure" else candidate["title"]
                body = candidate["fields"].get("System.Description", "") if self.provider == "azure" else candidate["body"]
                matches.append({"id": operation_id, "destination": self.store.prefix,
                    "payloadFingerprint": fingerprint({"title": title, "description": body, "kind": kind}),
                    "providerId": str(item_id(self.provider, candidate))})
            recovered = recover(operation, matches, complete)
            state["operations"][operation_id] = recovered
            self.store.commit(head, state)
            if recovered["state"] == "applied":
                self.record("recover-created-item-without-recreate", "passed", nativeId=recovered["providerId"], matches=len(matches), complete=complete, observations=attempt + 1)
                return recovered
            self.record("uncertain-create-observation", recovered["state"], matches=len(matches), complete=complete)
            if recovered["state"] == "conflict":
                return recovered
            # Read-only re-observation is safe. There is never another create here.
            time.sleep(2)
        return recovered

    def find_marker(self, marker):
        items = []
        pages = 0
        if self.provider == "azure":
            result = self.store.api.request("POST", f"/{self.store.project}/_apis/wit/wiql?$top=200", {
                "query": "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project ORDER BY [System.Id]",
            })
            identifiers = result["workItems"]
            for reference in identifiers:
                candidate = self.store.get_item(reference["id"])
                if marker in candidate["fields"].get("System.Description", ""):
                    items.append(candidate)
            return items, len(identifiers) < 200
        for page in range(1, 21):
            batch = self.store.api.request("GET", self.store.prefix + f"/issues?state=all&per_page=2&page={page}")
            pages += 1
            items.extend(item for item in batch if "pull_request" not in item and marker in (item.get("body") or ""))
            if len(batch) < 2:
                self.record("paginated-item-discovery", "passed", pages=pages)
                return items, True
        return items, False

    def work(self):
        first = self.create("human-edit")
        second = self.create("uncertain-create", lose_response=True)
        before = self.store.get_item(first)
        if self.provider == "azure":
            revised = self.store.conditional_description(first, before["rev"], "Human-authored revised acceptance; preserve me.")
            try:
                self.store.conditional_description(first, before["rev"], "Stale automated replacement")
            except ApiError as error:
                self.record("human-edit-revision-conflict", "observed", status=error.status, codes=error.codes)
            else:
                raise AssertionError("Stale Azure update succeeded")
            assert self.store.get_item(first)["fields"]["System.Description"] == "Human-authored revised acceptance; preserve me."
            relation_url = self.store.get_item(second)["url"]
            linked = self.store.api.request("PATCH", self.store.work_path(first), [
                {"op": "test", "path": "/rev", "value": revised["rev"]},
                {"op": "add", "path": "/relations/-", "value": {
                    "rel": "System.LinkTypes.Dependency-Forward", "url": relation_url,
                    "attributes": {"comment": "Synthetic integration prerequisite"}}},
                {"op": "add", "path": "/fields/System.Tags", "value": "area:phase0; coordination:review"},
            ], "application/json-patch+json")
            assert any(r["rel"] == "System.LinkTypes.Dependency-Forward" for r in linked["relations"])
            self.record("native-dependency-and-tags", "passed")
            comments = self.store.api.request("POST", self.store.work_path(first) + "/comments", {"text": "Synthetic human feedback; retained independently."}, api_version="7.1-preview.4")
            assert comments["id"]
            self.record("comment-created", "passed")
            history = self.store.api.request("GET", self.store.work_path(first) + "/updates?$top=1")
            assert len(history["value"]) == 1
            self.record("bounded-history-page", "passed", note="One-page response is not treated as complete history.")
            parent = self.create("hierarchy-parent", "Feature")
            current = self.store.get_item(first)
            self.store.api.request("PATCH", self.store.work_path(first), [
                {"op": "test", "path": "/rev", "value": current["rev"]},
                {"op": "add", "path": "/relations/-", "value": {"rel": "System.LinkTypes.Hierarchy-Reverse", "url": self.store.get_item(parent)["url"]}},
            ], "application/json-patch+json")
            assert any(r["rel"] == "System.LinkTypes.Hierarchy-Reverse" for r in self.store.get_item(first)["relations"])
            self.record("native-hierarchy", "passed")
            disposable = self.create("deletion-observation")
            self.store.api.request("DELETE", self.store.work_path(disposable))
            try:
                self.store.get_item(disposable)
            except ApiError as error:
                assert error.status in (404, 410)
                self.record("deleted-item-read", "passed", status=error.status,
                            note="Known deletion provenance; arbitrary 404 alone cannot distinguish deletion/access loss.")
            else:
                raise AssertionError("Deleted item still returned")
        else:
            self.store.api.request("PATCH", self.store.work_path(first), {"body": "Human-authored revised acceptance; preserve me."})
            try:
                self.store.conditional_description(first, before["updated_at"], "Stale replacement")
            except NotImplementedError:
                pass
            else:
                raise AssertionError("Unsafe GitHub replacement was not blocked")
            self.store.api.request("POST", self.store.work_path(first) + "/comments", {
                "body": "Program Kit proposed revision: retain human acceptance text and review the suggested change.",
            })
            assert self.store.get_item(first)["body"] == "Human-authored revised acceptance; preserve me."
            self.record("human-text-preserved-proposal-comment", "passed", note="Guarded adapter behavior; no claim of native issue CAS.")
            labels = self.store.api.request("GET", self.store.prefix + "/labels?per_page=100")
            if not any(label["name"] == "area:phase0" for label in labels):
                self.store.api.request("POST", self.store.prefix + "/labels", {"name": "area:phase0", "color": "0366d6"})
            self.store.api.request("POST", self.store.work_path(first) + "/labels", {"labels": ["area:phase0"]})
            self.record("native-label", "passed")
            self.store.api.request("POST", self.store.work_path(first) + "/sub_issues", {"sub_issue_id": self.store.get_item(second)["id"]})
            children = self.store.api.request("GET", self.store.work_path(first) + "/sub_issues")
            assert any(child["number"] == second for child in children)
            self.record("native-hierarchy", "passed")
            third = self.create("dependency-predecessor")
            self.store.api.request("POST", self.store.work_path(second) + "/dependencies/blocked_by", {"issue_id": self.store.get_item(third)["id"]})
            dependencies = self.store.api.request("GET", self.store.work_path(second) + "/dependencies/blocked_by")
            assert any(item["number"] == third for item in dependencies)
            self.record("native-dependency", "passed")

    def run(self, work_only=False):
        self.evidence["requestedSections"] = ["work"] if work_only else ["coordination", "work"]
        try:
            if not work_only:
                self.races()
            self.work()
            self.evidence["complete"] = True
        finally:
            self.evidence["finishedAt"] = datetime.now(timezone.utc).isoformat()
            self.save()
            print("Evidence: " + str(self.directory / "evidence.json"), flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("azure", "github") or sys.argv[2:] not in ([], ["--work-only"]):
        raise SystemExit("Choose azure or github, optionally --work-only; mutations stay in the approved probe scopes")
    Probe(sys.argv[1]).run(work_only=bool(sys.argv[2:]))
