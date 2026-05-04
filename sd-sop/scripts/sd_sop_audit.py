#!/usr/bin/env python3
"""Audit SD-SOP drift across GitHub PRs, git worktrees/branches, and Linear children.

This script is intentionally read-only. It shells out to git/gh/linear when available
and emits actionable findings rather than mutating state.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ISSUE_RE_DEFAULT = r"[A-Z][A-Z0-9]+-\d+"
ACTIVE_STATUS_NAMES = {"in progress", "in review", "started", "in development"}
DONE_STATUS_NAMES = {"done", "completed", "merged"}
GREEN_CONCLUSIONS = {"SUCCESS", "SKIPPED", "NEUTRAL"}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChildIssue:
    identifier: str
    title: str = ""
    status: str = ""
    status_type: str = ""
    branch_name: str = ""
    relations: list[dict[str, str]] = field(default_factory=list)


def run(cmd: list[str], cwd: str | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def load_json_cmd(cmd: list[str], cwd: str | None = None) -> Any | None:
    proc = run(cmd, cwd=cwd)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def infer_github_repo(repo_path: Path) -> str | None:
    data = load_json_cmd(["gh", "repo", "view", "--json", "nameWithOwner"], cwd=str(repo_path))
    if isinstance(data, dict):
        return data.get("nameWithOwner")
    return None


def default_branch(repo_path: Path, github_repo: str | None) -> str:
    if github_repo:
        data = load_json_cmd(["gh", "repo", "view", github_repo, "--json", "defaultBranchRef"], cwd=str(repo_path))
        try:
            name = data["defaultBranchRef"]["name"]
            if name:
                return name
        except Exception:
            pass
    proc = run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=str(repo_path))
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip().rsplit("/", 1)[-1]
    return "main"


def parse_worktrees(repo_path: Path) -> list[dict[str, str]]:
    proc = run(["git", "worktree", "list", "--porcelain"], cwd=str(repo_path))
    if proc.returncode != 0:
        return []
    items: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if not line:
            if cur:
                items.append(cur)
                cur = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree" and cur:
            items.append(cur)
            cur = {}
        cur[key] = value
    if cur:
        items.append(cur)
    return items


def gone_branches(repo_path: Path) -> list[str]:
    proc = run(["git", "branch", "-vv"], cwd=str(repo_path))
    if proc.returncode != 0:
        return []
    branches: list[str] = []
    for line in proc.stdout.splitlines():
        if ": gone]" in line:
            parts = line.replace("*", " ").split()
            if parts:
                branches.append(parts[0])
    return branches


def issue_refs(text: str, pattern: re.Pattern[str]) -> set[str]:
    return {m.group(0).upper() for m in pattern.finditer(text or "")}


def fetch_open_prs(repo_path: Path, github_repo: str, author: str, limit: int) -> list[dict[str, Any]]:
    fields = "number,title,url,headRefName,baseRefName,mergeable,mergeStateStatus,autoMergeRequest,statusCheckRollup,body"
    data = load_json_cmd([
        "gh", "pr", "list", "--author", author, "--state", "open", "--repo", github_repo,
        "--json", fields, "--limit", str(limit)
    ], cwd=str(repo_path))
    if isinstance(data, list):
        return data

    # Older gh versions may not allow body in pr list; fetch bodies one by one.
    fields = "number,title,url,headRefName,baseRefName,mergeable,mergeStateStatus,autoMergeRequest,statusCheckRollup"
    data = load_json_cmd([
        "gh", "pr", "list", "--author", author, "--state", "open", "--repo", github_repo,
        "--json", fields, "--limit", str(limit)
    ], cwd=str(repo_path))
    prs = data if isinstance(data, list) else []
    for pr in prs:
        view = load_json_cmd(["gh", "pr", "view", str(pr.get("number")), "--repo", github_repo, "--json", "body"], cwd=str(repo_path))
        pr["body"] = view.get("body", "") if isinstance(view, dict) else ""
    return prs


def check_summary(pr: dict[str, Any]) -> tuple[list[str], list[str], bool]:
    failures: list[str] = []
    pending: list[str] = []
    checks = pr.get("statusCheckRollup") or []
    for item in checks:
        if item.get("__typename") != "CheckRun":
            continue
        name = item.get("name") or "<unnamed>"
        status = item.get("status") or ""
        conclusion = item.get("conclusion") or ""
        if status != "COMPLETED":
            pending.append(name)
        elif conclusion and conclusion not in GREEN_CONCLUSIONS:
            failures.append(name)
    green = not failures and not pending and bool(checks)
    return failures, pending, green


def linear_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any] | None:
    key = os.environ.get("LINEAR_API_KEY")
    if not key:
        return None
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_linear_children(parent_id: str) -> dict[str, ChildIssue]:
    query = """
    query($id:String!){
      issue(id:$id){
        children(first:100){ nodes{
          identifier title branchName
          state{ name type }
          relations(first:50){ nodes{ type relatedIssue{ identifier title } } }
          inverseRelations(first:50){ nodes{ type issue{ identifier title } } }
        }}
      }
    }
    """
    data = linear_graphql(query, {"id": parent_id})
    nodes = (((data or {}).get("data") or {}).get("issue") or {}).get("children", {}).get("nodes")
    children: dict[str, ChildIssue] = {}
    if isinstance(nodes, list):
        for node in nodes:
            state = node.get("state") or {}
            issue = ChildIssue(
                identifier=(node.get("identifier") or "").upper(),
                title=node.get("title") or "",
                status=state.get("name") or "",
                status_type=state.get("type") or "",
                branch_name=node.get("branchName") or "",
            )
            for rel in node.get("relations", {}).get("nodes", []) or []:
                related = rel.get("relatedIssue") or {}
                if related.get("identifier"):
                    issue.relations.append({"type": rel.get("type") or "", "issue": related["identifier"].upper()})
            for rel in node.get("inverseRelations", {}).get("nodes", []) or []:
                related = rel.get("issue") or {}
                if related.get("identifier"):
                    # Normalize inverse relations from the child's perspective.
                    t = rel.get("type") or ""
                    inv = {"blocks": "blocked_by", "blocked_by": "blocks"}.get(t, t)
                    issue.relations.append({"type": inv, "issue": related["identifier"].upper()})
            if issue.identifier:
                children[issue.identifier] = issue
        return children

    data = load_json_cmd(["linear", "issue", "get", parent_id])
    if isinstance(data, dict):
        for node in data.get("children") or []:
            ident = (node.get("identifier") or "").upper()
            if ident:
                children[ident] = ChildIssue(
                    identifier=ident,
                    title=node.get("title") or "",
                    status=node.get("status") or "",
                    status_type=node.get("statusType") or "",
                )
    return children


def has_dependency(child: ChildIssue, other_ids: set[str]) -> bool:
    for rel in child.relations:
        if rel.get("issue") in other_ids and rel.get("type") in {"blocked_by", "blocks", "related"}:
            return True
    return False


def audit_repo(repo_path: Path, github_repo: str | None, args: argparse.Namespace, children: dict[str, ChildIssue], issue_pattern: re.Pattern[str]) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    repo_path = repo_path.resolve()
    if not github_repo:
        github_repo = infer_github_repo(repo_path)
    if not github_repo:
        findings.append(Finding("error", "github_repo_unknown", f"Could not infer GitHub repo for {repo_path}"))
        return findings, {"repoPath": str(repo_path)}

    base = default_branch(repo_path, github_repo)
    prs = fetch_open_prs(repo_path, github_repo, args.author, args.pr_limit)
    worktrees = parse_worktrees(repo_path)
    gone = gone_branches(repo_path)

    if len(worktrees) > args.max_worktrees:
        findings.append(Finding(
            "warn", "worktree_limit_exceeded",
            f"{github_repo} has {len(worktrees)} worktrees; limit is {args.max_worktrees}",
            {"worktrees": [w.get("worktree") for w in worktrees]},
        ))

    if gone:
        findings.append(Finding(
            "info", "gone_local_branches",
            f"{github_repo} has local branches whose upstream is gone",
            {"branches": gone},
        ))

    pr_issue_refs: dict[int, set[str]] = {}
    head_to_pr_refs: dict[str, set[str]] = {}
    for pr in prs:
        text = "\n".join(str(pr.get(k) or "") for k in ("title", "headRefName", "body"))
        refs = issue_refs(text, issue_pattern)
        pr_issue_refs[int(pr["number"])] = refs
        if pr.get("headRefName"):
            head_to_pr_refs[pr["headRefName"]] = refs

        failures, pending, green = check_summary(pr)
        number = pr.get("number")
        if failures:
            findings.append(Finding("error", "pr_checks_failed", f"PR #{number} has failing checks", {"checks": failures, "url": pr.get("url")}))
        if pr.get("mergeStateStatus") == "DIRTY" or pr.get("mergeable") == "CONFLICTING":
            findings.append(Finding("error", "pr_dirty", f"PR #{number} is dirty/conflicting", {"url": pr.get("url")}))
        if green and pr.get("mergeable") == "MERGEABLE" and pr.get("mergeStateStatus") in {"CLEAN", "HAS_HOOKS", "UNKNOWN"} and not pr.get("autoMergeRequest"):
            findings.append(Finding("warn", "green_pr_no_automerge", f"PR #{number} is green/mergeable but auto-merge is not armed", {"url": pr.get("url")}))

        child_refs = refs & set(children.keys()) if children else refs
        if len(child_refs) > 1:
            findings.append(Finding("error", "pr_multiple_issue_children", f"PR #{number} references multiple implementation issues", {"issues": sorted(child_refs), "url": pr.get("url")}))

        base_ref = pr.get("baseRefName") or ""
        if base_ref and base_ref != base:
            base_refs = head_to_pr_refs.get(base_ref, set())
            current_child_refs = child_refs
            dependency_ok = False
            if children and base_refs and current_child_refs:
                for cid in current_child_refs:
                    child = children.get(cid)
                    if child and has_dependency(child, base_refs):
                        dependency_ok = True
            elif "stack" in (pr.get("body") or "").lower():
                dependency_ok = True
            if not dependency_ok:
                findings.append(Finding("error", "stacked_pr_missing_dependency", f"PR #{number} is stacked on {base_ref} without a verified dependency relation", {"url": pr.get("url"), "baseRefName": base_ref}))

    summary = {
        "repoPath": str(repo_path),
        "githubRepo": github_repo,
        "defaultBranch": base,
        "openPrCount": len(prs),
        "worktreeCount": len(worktrees),
        "goneBranchCount": len(gone),
        "openPrIssueRefs": {str(number): sorted(refs) for number, refs in pr_issue_refs.items()},
        "openPrHeadRefs": [pr.get("headRefName") for pr in prs if pr.get("headRefName")],
    }
    return findings, summary


def print_human(findings: list[Finding], summaries: list[dict[str, Any]]) -> None:
    print("SD-SOP audit")
    for s in summaries:
        print(f"- {s.get('githubRepo', s.get('repoPath'))}: {s.get('openPrCount', 0)} open PRs, {s.get('worktreeCount', 0)} worktrees, {s.get('goneBranchCount', 0)} gone local branches")
    if not findings:
        print("\nNo SD-SOP drift found.")
        return
    print("\nFindings:")
    for f in findings:
        details = f" {json.dumps(f.details, sort_keys=True)}" if f.details else ""
        print(f"- [{f.severity}] {f.code}: {f.message}{details}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only SD-SOP audit for issue→PR mapping, PR health, dependencies, and worktree hygiene.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          sd_sop_audit.py --repo ~/src/clamshell-ai/desktop --github-repo clamshell-ai/desktop --linear-parent CLAI-1184 --author ujjaval-verma
          sd_sop_audit.py --repo . --author @me --max-worktrees 4 --json
        """),
    )
    parser.add_argument("--repo", action="append", default=[], help="Local git repo path. Repeatable. Defaults to cwd.")
    parser.add_argument("--github-repo", action="append", default=[], help="GitHub owner/name. Repeatable; paired by order with --repo when provided.")
    parser.add_argument("--linear-parent", action="append", default=[], help="Linear parent issue id. Repeatable; children are audited as implementation slices.")
    parser.add_argument("--author", default="@me", help="GitHub PR author filter. Use ujjaval-verma for Ujju-owned lanes.")
    parser.add_argument("--issue-regex", default=ISSUE_RE_DEFAULT, help="Issue id regex used to parse PR titles/bodies/branches.")
    parser.add_argument("--max-worktrees", type=int, default=4, help="Maximum allowed git worktrees per repo.")
    parser.add_argument("--pr-limit", type=int, default=50, help="Max open PRs to fetch per repo.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human text.")
    parser.add_argument("--fail-on-findings", action="store_true", help="Exit 1 when any warn/error finding exists.")
    args = parser.parse_args()

    issue_pattern = re.compile(args.issue_regex)
    repo_paths = [Path(p).expanduser() for p in (args.repo or [os.getcwd()])]
    github_repos = args.github_repo

    children: dict[str, ChildIssue] = {}
    for parent in args.linear_parent:
        children.update(fetch_linear_children(parent))

    all_findings: list[Finding] = []
    summaries: list[dict[str, Any]] = []
    for i, repo_path in enumerate(repo_paths):
        gh_repo = github_repos[i] if i < len(github_repos) else None
        findings, summary = audit_repo(repo_path, gh_repo, args, children, issue_pattern)
        all_findings.extend(findings)
        summaries.append(summary)

    if children:
        refs_to_open_prs: dict[str, list[str]] = {cid: [] for cid in children}
        all_open_heads: set[str] = set()
        for summary in summaries:
            repo_name = summary.get("githubRepo") or summary.get("repoPath") or "repo"
            all_open_heads.update(h for h in summary.get("openPrHeadRefs", []) if h)
            for number, refs in (summary.get("openPrIssueRefs") or {}).items():
                for cid in set(refs) & set(children.keys()):
                    refs_to_open_prs.setdefault(cid, []).append(f"{repo_name}#{number}")
        for cid, child in children.items():
            status = (child.status or child.status_type or "").lower()
            active = any(s in status for s in ACTIVE_STATUS_NAMES)
            if active and not refs_to_open_prs.get(cid):
                all_findings.append(Finding("warn", "active_issue_no_open_pr", f"{cid} is active but no open PR references it", {"status": child.status, "title": child.title}))
            if active and child.branch_name and child.branch_name not in all_open_heads:
                all_findings.append(Finding("info", "active_issue_branch_no_open_pr", f"{cid} has tracker branchName but no matching open PR", {"branchName": child.branch_name, "status": child.status}))

    if args.json:
        print(json.dumps({
            "summaries": summaries,
            "children": {k: v.__dict__ for k, v in children.items()},
            "findings": [f.__dict__ for f in all_findings],
        }, indent=2, sort_keys=True))
    else:
        print_human(all_findings, summaries)

    if args.fail_on_findings and any(f.severity in {"warn", "error"} for f in all_findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
