"""Advertise only a stable release whose complete Release workflow succeeded."""
import json
import os
from pathlib import Path
import re
import urllib.request

REPOSITORY = "orbyss-io/program-kit"
START = "<!-- latest-published-release:start -->"
END = "<!-- latest-published-release:end -->"
VERSION = r"\d+\.\d+\.\d+"


def api(path):
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/{path}",
        headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}",
                 "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def published_version(event):
    release = api("releases/latest")
    tag = release["tag_name"]
    if release["draft"] or release["prerelease"] or not re.fullmatch(f"v{VERSION}", tag):
        raise ValueError("The latest release must be a published stable semantic version")
    commit = api(f"commits/{tag}")["sha"]
    if "workflow_run" in event:
        runs = [event["workflow_run"]]
        # A delayed older completion must never roll back the current README.
        if runs[0]["head_branch"] != tag:
            return None
    else:
        runs = api(f"actions/workflows/release.yml/runs?event=push&status=success&head_sha={commit}&per_page=100")["workflow_runs"]
    if not any(run["name"] == "Release" and run["event"] == "push"
               and run["conclusion"] == "success" and run["head_sha"] == commit
               and run["head_branch"] == tag
               and run["head_repository"]["full_name"] == REPOSITORY for run in runs):
        raise ValueError(f"{tag} has no successful complete Release workflow at its tag commit")
    return tag[1:]


def update_text(text, version):
    if not re.fullmatch(VERSION, version):
        raise ValueError("Invalid release version")
    pattern = re.compile(re.escape(START) + r"\n.*?\n" + re.escape(END), re.DOTALL)
    if len(pattern.findall(text)) != 1:
        raise ValueError("README must contain exactly one latest-published-release block")
    block = (f"{START}\nLatest available release: **[v{version}]"
             f"(https://github.com/{REPOSITORY}/releases/tag/v{version})**. "
             f"[Check the latest release](https://github.com/{REPOSITORY}/releases/latest) "
             "before installing; use its assets rather than an older cached version.\n"
             f"{END}")
    text = pattern.sub(lambda _: block, text)
    if tuple(map(int, version.split('.'))) > (0, 12, 9):
        text = re.sub(r"<!-- initializer-hotfix:start -->\n.*?\n<!-- initializer-hotfix:end -->\n\n",
                      "", text, flags=re.DOTALL)
    # Only kit install/upgrade/verification examples; retain historical explanations
    # and independently versioned dependencies and qualification profiles.
    text = re.sub(rf"(releases/download/v){VERSION}(?=/Initialize-ProgramKit-)",
                  lambda m: m[1] + version, text)
    text = re.sub(rf"(Initialize-ProgramKit-){VERSION}(?=\.(?:cmd|sh))",
                  lambda m: m[1] + version, text)
    text = re.sub(rf"(program-kit-){VERSION}(?=[\\/\s.]|$)",
                  lambda m: m[1] + version, text)
    return text


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    version = published_version(event)
    if version is None:
        print("An older Release run completed; keeping the latest available version")
        return
    readme = Path("README.md")
    text = readme.read_text(encoding="utf-8")
    updated = update_text(text, version)
    if updated != text:
        readme.write_text(updated, encoding="utf-8")
    print(f"README latest available release: v{version}")


if __name__ == "__main__":
    main()
