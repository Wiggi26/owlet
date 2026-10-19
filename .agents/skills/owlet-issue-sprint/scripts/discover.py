"""Read-only Owlet discovery and conservative batch proposals; standard library only."""

import argparse
import fnmatch
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = "Wiggi26/owlet"
CAP = 10000
BUSY = {
    "agent:in-progress",
    "agent:blocked",
    "agent:needs-review",
    "agent:needs-manual-test",
}


def command(*args):
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{args[0]} {args[1]} failed; discovery is incomplete")
    return result.stdout


def gh(*args):
    if args[:2] == ("repo", "view"):
        return json.loads(command("gh", "repo", "view", REPO, *args[2:]))
    return json.loads(command("gh", *args, "--repo", REPO))


def listing(kind, fields):
    items = gh(kind, "list", "--state", "all", "--limit", str(CAP), "--json", fields)
    if len(items) >= CAP:
        raise RuntimeError("Listing cap reached; completeness cannot be established")
    return items


def api_pages(path):
    # gh api has no --repo flag. Always use this literal fork endpoint.
    pages = json.loads(
        command(
            "gh",
            "api",
            "--hostname",
            "github.com",
            "--paginate",
            "--slurp",
            f"repos/{REPO}/{path}?per_page=100",
        )
    )
    if not all(isinstance(page, list) for page in pages):
        raise RuntimeError("Unexpected paginated response")
    return [item for page in pages for item in page]


def discover():
    repo = gh(
        "repo", "view", "--json", "name,owner,viewerPermission,defaultBranchRef,url"
    )
    if (repo["owner"]["login"], repo["name"]) != ("Wiggi26", "owlet"):
        raise RuntimeError("Repository identity mismatch")
    issues = listing("issue", "number,title,body,state,labels,url,updatedAt")
    prs = listing(
        "pr",
        "number,title,body,state,url,headRefName,baseRefName,mergedAt,closingIssuesReferences",
    )
    for issue in issues:
        if issue["state"].upper() == "OPEN":
            issue.update(
                gh(
                    "issue",
                    "view",
                    str(issue["number"]),
                    "--json",
                    "closedByPullRequestsReferences",
                )
            )
            issue["comments"] = api_pages(f"issues/{issue['number']}/comments")
            blockers = api_pages(f"issues/{issue['number']}/dependencies/blocked_by")
            if any(
                not item["html_url"].startswith(f"https://github.com/{REPO}/issues/")
                for item in blockers
            ):
                raise RuntimeError("Cross-repository prerequisite needs manual review")
            issue["blocked_by"] = [item["number"] for item in blockers]
    labels = gh(
        "label", "list", "--limit", str(CAP), "--json", "name,description,color"
    )
    if len(labels) >= CAP:
        raise RuntimeError("Label listing cap reached")
    return {
        "repository": REPO,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "complete": True,
        "repo": repo,
        "issues": issues,
        "prs": prs,
        "labels": labels,
        "branches": [item["name"] for item in api_pages("branches")],
        "local_branches": command(
            "git", "for-each-ref", "--format=%(refname:short)", "refs/heads"
        ).splitlines(),
        "worktrees": command("git", "worktree", "list", "--porcelain"),
    }


def dependencies(issue):
    section = issue["body"].split("## Dependencies", 1)
    if len(section) != 2:
        return None
    section = section[1].split("\n## ", 1)[0]
    found = {
        int(n) for n in re.findall(r"github\.com/Wiggi26/owlet/issues/(\d+)", section)
    }
    if not found and "No open issue prerequisite" not in section:
        return None
    return found | set(issue["blocked_by"])


def overlaps(left, right):
    return any(
        fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a)
        for a in left
        for b in right
    )


def references_issue(pr, number, findings):
    text = pr["title"] + " " + pr["body"]
    return (
        any(ref["number"] == number for ref in pr.get("closingIssuesReferences", []))
        or re.search(rf"(?<![\w/])#{number}(?!\d)", text)
        or re.search(rf"github\.com/{REPO}/issues/{number}(?!\d)", text)
        or any(f in text for f in findings)
        or re.search(rf"issue[-/]{number}(?:[-/]|$)", pr["headRefName"])
    )


def select(snapshot, audit, roadmap, plan, limit):
    if snapshot.get("repository") != REPO or snapshot.get("complete") is not True:
        raise ValueError("Require a complete fork snapshot")
    if plan.get("repository", REPO) != REPO:
        raise ValueError("Touch plan repository mismatch")
    register = audit.split("## Historical audit", 1)[0]
    mapped = {}
    for line in register.splitlines():
        if line.startswith("| <a id="):
            number = re.search(r"github\.com/Wiggi26/owlet/issues/(\d+)", line)
            if number:
                mapped.setdefault(int(number[1]), []).append(line.split("|")[4].strip())
    issues = {item["number"]: item for item in snapshot["issues"]}
    ranked, deferred = [], []
    for number, issue in issues.items():
        if issue["state"].upper() != "OPEN":
            continue
        findings = sorted(set(re.findall(r"OWL-\d{3}", issue["body"])))
        deps = dependencies(issue)
        priority = re.search(r"\*\*Priority:\*\* P([123])", issue["body"])
        labels = {item["name"] for item in issue["labels"]}
        reason = None
        if number not in mapped or not findings:
            reason = "missing current audit mapping"
        elif (
            "## Acceptance criteria" not in issue["body"]
            or deps is None
            or not priority
        ):
            reason = "missing or ambiguous criteria/priority/dependencies"
        elif labels & BUSY:
            reason = "existing agent state requires coordinator review"
        elif deps:
            unmet = []
            for dep in sorted(deps):
                dep_findings = re.findall(
                    r"OWL-\d{3}", issues.get(dep, {}).get("body", "")
                )
                merged = any(
                    pr.get("mergedAt") and references_issue(pr, dep, dep_findings)
                    for pr in snapshot["prs"]
                )
                if (
                    dep not in issues
                    or issues[dep]["state"].upper() != "CLOSED"
                    or set(mapped.get(dep, [])) != {"Resolved"}
                    or not merged
                ):
                    unmet.append(dep)
            if unmet:
                reason = f"unverified prerequisites: {unmet}"
        existing = []
        for pr in snapshot["prs"]:
            if pr["state"].upper() != "OPEN":
                continue
            if references_issue(pr, number, findings):
                existing.append(f"PR #{pr['number']}")
        for branch in snapshot["branches"] + snapshot.get("local_branches", []):
            if re.search(rf"issue[-/]{number}(?:[-/]|$)", branch) or any(
                f.lower() in branch.lower() for f in findings
            ):
                existing.append(branch)
        if existing:
            reason = f"existing work: {sorted(set(existing))}"
        scope = plan.get("issues", {}).get(str(number))
        if not reason and (
            not scope or not scope.get("scope") or not scope.get("paths")
        ):
            reason = "needs coordinator-reviewed scope and touch paths"
        if not reason and scope.get("model") not in {"gpt-6-luna", "gpt-6.1-sol"}:
            reason = "needs a supported coordinator-reviewed model route"
        if reason:
            deferred.append({"issue": number, "reason": reason})
            continue
        position = roadmap.find(f"https://github.com/{REPO}/issues/{number})")
        ranked.append(
            {
                "issue": number,
                "findings": findings,
                "priority": int(priority[1]),
                "roadmap_order": position if position >= 0 else len(roadmap),
                "scope": scope["scope"],
                "paths": scope["paths"],
                "model": scope["model"],
            }
        )
    selected = []
    for item in sorted(
        ranked, key=lambda x: (x["priority"], x["roadmap_order"], x["issue"])
    ):
        if len(selected) >= limit:
            deferred.append({"issue": item["issue"], "reason": "batch limit"})
        elif any(overlaps(item["paths"], other["paths"]) for other in selected):
            deferred.append(
                {
                    "issue": item["issue"],
                    "reason": "overlapping planned files; serialize",
                }
            )
        else:
            selected.append(item)
    return {
        "mode": "read-only proposal; no claims",
        "selected": selected,
        "deferred": deferred,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot", type=Path, help="Replay a saved snapshot without network"
    )
    parser.add_argument(
        "--save", type=Path, help="Save public discovery outside tracked files"
    )
    parser.add_argument(
        "--plan", type=Path, help="Fresh coordinator-reviewed touch plan JSON"
    )
    parser.add_argument("--limit", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    snapshot = (
        json.loads(args.snapshot.read_text(encoding="utf-8"))
        if args.snapshot
        else discover()
    )
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    plan = json.loads(args.plan.read_text(encoding="utf-8")) if args.plan else {}
    report = select(
        snapshot,
        (root / "docs/AUDIT.md").read_text(encoding="utf-8"),
        (root / "docs/ROADMAP.md").read_text(encoding="utf-8"),
        plan,
        args.limit,
    )
    print(json.dumps({"captured_at": snapshot["captured_at"], **report}, indent=2))


if __name__ == "__main__":
    main()
