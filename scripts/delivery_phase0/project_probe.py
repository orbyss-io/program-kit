"""Probe fields only in the approved private GitHub Project; no org type edits."""
import json

from .probe import Probe
from .setup import JOURNAL, create_once


def main():
    probe = Probe("github")
    journal = json.loads(JOURNAL.read_text())
    project_id = journal["resources"]["github_project"]["value"]["id"]
    api = probe.store.api
    project = api.graphql("query($id:ID!){node(id:$id){... on ProjectV2{id public shortDescription fields(first:100){nodes{... on ProjectV2FieldCommon{id name dataType}} pageInfo{hasNextPage}}}}}", {"id": project_id})["node"]
    marker = "Program Kit disposable Phase 0; setup=" + journal["setup_id"]
    assert project["public"] is False and project["shortDescription"] == marker
    assert not project["fields"]["pageInfo"]["hasNextPage"]
    probe.record("project-capability-discovery", "passed", fields=project["fields"]["nodes"])
    try:
        field = create_once(journal, "github_probe_field", lambda: api.graphql(
            "mutation($project:ID!){createProjectV2Field(input:{projectId:$project,dataType:TEXT,name:\"Program Kit Probe Revision\"}){projectV2Field{... on ProjectV2Field{id name}}}}",
            {"project": project_id})["createProjectV2Field"]["projectV2Field"])
        native = probe.create("project-member")
        issue = probe.store.get_item(native)
        item = api.graphql("mutation($project:ID!,$content:ID!){addProjectV2ItemById(input:{projectId:$project,contentId:$content}){item{id}}}",
            {"project": project_id, "content": issue["node_id"]})["addProjectV2ItemById"]["item"]
        api.graphql("mutation($project:ID!,$item:ID!,$field:ID!){updateProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,fieldId:$field,value:{text:\"basis-v1\"}}){projectV2Item{id}}}",
            {"project": project_id, "item": item["id"], "field": field["id"]})
        readback = api.graphql("query($id:ID!){node(id:$id){... on ProjectV2Item{id content{... on Issue{id number}} fieldValues(first:100){nodes{... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2Field{id name}}}} pageInfo{hasNextPage}}}}}", {"id": item["id"]})["node"]
        assert readback["content"]["number"] == native
        assert not readback["fieldValues"]["pageInfo"]["hasNextPage"]
        assert any(value.get("field", {}).get("id") == field["id"] and value.get("text") == "basis-v1" for value in readback["fieldValues"]["nodes"])
        probe.record("project-field-write-and-read", "passed", projectId=project_id, itemId=item["id"], issueId=issue["node_id"], fieldId=field["id"],
                     note="Distinct Project/item/issue identities verified; this API is not a CAS.")
        disposable = probe.create("github-deletion-observation")
        target = probe.store.get_item(disposable)
        api.graphql("mutation($id:ID!){deleteIssue(input:{issueId:$id}){repository{id}}}", {"id": target["node_id"]})
        from .transport import ApiError
        try:
            probe.store.get_item(disposable)
        except ApiError as error:
            assert error.status in (404, 410)
            probe.record("deleted-item-read", "passed", status=error.status)
        else:
            raise AssertionError("Deleted synthetic issue still returned")
        probe.evidence["complete"] = True
    finally:
        probe.evidence["requestedSections"] = ["project-fields", "deletion"]
        probe.save()
        print("Evidence: " + str(probe.directory / "evidence.json"))


if __name__ == "__main__":
    main()
