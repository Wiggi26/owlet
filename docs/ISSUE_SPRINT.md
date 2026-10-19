# Running an Owlet issue sprint

This workflow handles one incremental batch in `Wiggi26/owlet`. The reusable
[skill](../.agents/skills/owlet-issue-sprint/SKILL.md) governs execution;
[AGENTS.md](../AGENTS.md), the [audit](AUDIT.md), [roadmap](ROADMAP.md) and
[testing profiles](TESTING.md) remain authoritative. Creating this workflow does
not implement or resolve any of the 23 remediation issues.

## Start from the Codex desktop app

1. Open the Owlet project on a checkout containing this setup. Review/trust the
   project configuration through the normal app flow. Repository skills are
   discovered in `.agents/skills`; if the skill does not appear, restart Codex.
2. Use the model control beneath the composer to select GPT-6.1 Sol for complex
   coordination when available. Project defaults select GPT-6 Luna for ordinary
   subagents; the `owlet-complex` and `owlet-reviewer` roles select GPT-6.1 Sol.
   The project cap is three spawned agents, excluding the coordinator. The skill
   also caps active agents across the whole batch and prohibits nested fan-out.
3. Use the same prompt for each batch; there is no need to name individual issues:

   ```text
   Use $owlet-issue-sprint to implement the next safe remediation batch.
   ```

   To preview without writes:

   ```text
   Use $owlet-issue-sprint for a read-only dry run of the next batch.
   ```

   After implementation PRs merge and verification is available:

   ```text
   Use $owlet-issue-sprint to reconcile merged fixes and verification evidence.
   ```

4. Review the returned PRs and required manual checks. Merging remains a human
   decision. Repeat the batch prompt when ready; each invocation rediscovers the
   backlog and stops after one batch. No scheduler, deployment runner or API-key
   application is installed.

Model availability and usage limits depend on the signed-in account/client.
Plus does not imply an unlimited number of concurrent batches. If a requested
model is unavailable, report it and retain the appropriate risk boundary; do
not silently send complex fixes to Luna. Use the currently exposed native
subagent tools and their model overrides. Older clients that do not load the
project roles can receive explicit model instructions; if delegation is not
available, process fewer issues serially with a capable coordinator.

## Discovery and reproducible selection

Use an authenticated GitHub CLI (`gh auth login` if needed), Git and Python 3.12
or newer. The helper uses the standard library and adds no project dependencies.
Run it from the repository root:

```text
python .agents/skills/owlet-issue-sprint/scripts/discover.py --save .cache/owlet-sprints/backlog.json
```

This performs reads only. `gh issue/pr list --state all --limit 10000` follows
pagination to that cap and aborts if it is reached. Comments, labels, native
blocking relationships and branches are retrieved too; REST collections use
explicit pagination. All high-level repository commands use
`--repo Wiggi26/owlet`. `gh api` does not support that flag, so the helper uses
only literal `repos/Wiggi26/owlet/...` endpoints and `--hostname github.com`.
An error aborts discovery rather than producing an apparently complete plan.

Read all open issue bodies and comments in the saved snapshot. Compare the
current audit register and roadmap with the actual source/test paths. Review
native dependencies, comments, manual gates and PRs whose arbitrary names may
not be detected by a naming heuristic. The helper intentionally requires a
coordinator-reviewed touch plan before it selects anything. It is a proposal
tool, not an autonomous issue claimant or a semantic dependency solver.

Create an untracked JSON plan such as `.cache/owlet-sprints/touch-plan.json`:

```json
{
  "repository": "Wiggi26/owlet",
  "issues": {
    "3": {
      "scope": "OWL-001/002 only: options constructor and absent interval default",
      "model": "gpt-6-luna",
      "paths": [
        "custom_components/owlet/config_flow.py",
        "custom_components/owlet/__init__.py",
        "custom_components/owlet/coordinator.py",
        "tests/test_config_flow.py",
        "tests/test_init.py",
        "tests/test_coordinator.py"
      ]
    }
  }
}
```

This is a format example, not a permanent assignment. Include every intended
edit, including shared fixtures; use `*` for unknown scope to prevent parallel
assignment. Use exact files or simple file globs; manually review intersecting
wildcards and semantic conflicts. Do not add shared tracking documents to worker
touch plans. A scope/model in a local JSON file is a coordinator decision, not
proof that a model has access or that a defect is reproduced.

```text
python .agents/skills/owlet-issue-sprint/scripts/discover.py --snapshot .cache/owlet-sprints/backlog.json --plan .cache/owlet-sprints/touch-plan.json --limit 3
```

Offline replay is for testing or inspection. Refresh live discovery before
claiming. The helper ranks priority then roadmap order, rejects known existing
work, unmet prerequisites and overlapping planned files, and proposes at most
three assignments. A prerequisite needs a merged linked fix and all mapped
audit findings Resolved; closure alone cannot unblock it. This conservative
check can defer a partially completed grouped issue even when one prerequisite
is satisfied. The coordinator may document that narrow evidence explicitly and
make a smaller reviewed assignment; never blindly override a blocker.

Snapshots/assignment records belong under the already ignored `.cache/`, not in
Git. Store public metadata and synthetic verification only. Never save account
credentials, real cloud responses or household data there as part of this work.

## Labels and ownership

Reuse existing labels; create only missing definitions with
`gh label create --repo Wiggi26/owlet`. Do not overwrite existing meanings or
remove human classification/priority labels. Verify owner/name/access before
each label creation, issue edit, comment, push or PR write.

| Label | Meaning / transition |
| --- | --- |
| `audit` | Stable link to the audit backlog; keep through resolution. |
| `agent:ready` | Dependencies permit an offline scope; unclaimed, subject to live recheck. |
| `agent:in-progress` | Coordinator owns a recorded assignment and a worker is active. |
| `agent:blocked` | Named dependency, evidence gap, failed check or unavailable required capability prevents progress. |
| `agent:needs-review` | PR/evidence handed off for review; issue remains open. |
| `agent:needs-manual-test` | Additional flag for outstanding owner-run acceptance; may coexist with review/blocked state. |

Keep exactly one of ready/in-progress/blocked/needs-review when triaged. Ready
does not guarantee a whole grouped issue fits one PR. Pending manual acceptance
must not cause a second agent to reimplement an existing fix. Replace state
labels serially and preserve unrelated labels. Explain blockers and transitions
in a concise issue comment when they change; avoid repeated unchanged comments.
After merged evidence satisfies all criteria, the coordinator can reconcile and
close the issue, removing obsolete agent-state/manual flags. If only part is
merged, keep it open and identify the next remaining scope.

## Exclusive claim and assignment protocol

Only one coordinator may dispatch a sprint at a time, including across desktop
chats/computers. Labels cannot provide atomic exclusion. In implementation mode:

1. Verify `gh repo view Wiggi26/owlet --json name,owner,viewerPermission` resolves
   exactly to the fork with write access. Read current fork main's commit.
2. **Create**, never update, `refs/heads/codex/issue-sprint-lock` at that commit
   using the GitHub create-ref operation. For CLI this is
   `gh api --hostname github.com --method POST repos/Wiggi26/owlet/git/refs`
   with `ref=refs/heads/codex/issue-sprint-lock` and the verified main `sha`.
   A structured create-branch tool is also suitable only if it is create-only
   and explicitly targets `Wiggi26/owlet`. Existing ref / HTTP 422 means another
   claim or an interrupted sprint: stop dispatch; do not overwrite or steal it.
3. After acquiring the ref, refresh issues, PRs, branches and worktrees. Record
   a UTC batch ID, coordinator chat/session identifier, base commit, issue/finding
   scope, acceptance criteria, assigned agent/model, absolute worktree, branch,
   allowed paths and checks in an untracked assignment record. Publish concise
   assignment details in each selected issue, then set in-progress before any
   worker starts. If a claim write fails, do not dispatch that assignment.
4. The coordinator creates each independent worktree from fork main; use
   `git worktree add` or the desktop managed-worktree tool, verifying the returned
   absolute path. A local worktree is sufficient; a separate user-owned chat is
   unnecessary. Check for existing issue/finding branches and PRs before creating
   anything; recover existing work with its owner instead of duplicating it.
5. Workers never claim, label, comment, push, create PRs, switch another worker's
   branch or edit shared audit/roadmap tracking. In their own worktree they may
   investigate/edit/run checks; the coordinator serialises commits and all
   external writes. Pass each worker the user-authorised mode and full assignment.
6. Release the claim after all workers stop and each assignment has a durable
   PR/issue handoff. Reverify repository/access and lock SHA/ownership before
   deleting that specific lock ref. Never delete an issue branch as cleanup.
   Interrupted claims have no automatic time expiry: inspect the recorded owner,
   active agents, worktrees and issue/PR evidence before an explicitly approved
   recovery. Do not auto-clear in-progress labels based on age.

The lock ref is only an ownership marker; no code is committed to it and no PR is
opened from it. Dry runs do not create a lock or change labels. The setup task
creates label definitions/triage only and does not acquire an implementation claim.

## Verification and handoff

Follow [TESTING.md](TESTING.md) for locked Linux commands and the exact paired
Core/Python profiles. Relevant regressions must fail before and pass after the
fix. Use the existing Actions workflow for all six jobs: Ruff/workflow security,
both runtime profiles, dependency advisories, hassfest and HACS. On Windows use
Linux/WSL for runtime checks. Do not fabricate local container results when only
hosted validators ran. If checks cannot run, state that and keep the PR pending
or draft. Review high-risk changes with the Sol reviewer after a worker slot is
free. Preserve assertions and validation even when the baseline has failures.

Before push verify `git remote get-url --push origin` and the resolved owner/name;
push to the verified fork URL only. Before PR creation verify both head and base
belong to `Wiggi26/owlet`, with base `main`. Use
`gh pr create --repo Wiggi26/owlet --base main --head <verified-branch>` and
`--body-file` for multiline descriptions. Avoid auto-close wording; use `Refs #N`
and OWL IDs. Link the PR in its issue and attach it to the Codex chat. Inspect
the latest PR head and all check results, not a superseded green run. Report
pending/failing checks as such and keep incomplete verification explicit.

Summarise attempted issues/scopes, PR-ready work, merged/verified work (if any),
PR links, exact-head CI links/status, blockers, outstanding manual checks and
the recommended next batch. Never call code generation, strict xfails, metadata
success or an unmerged PR a resolved runtime defect. Manual tests are privately
owner-run after separate approval; installation uses HACS. No HA/Proxmox access,
deployment, release publication, automatic merge or official alarm changes occur.

## Setup verification record

The setup PR records a read-only live discovery and offline selection exercises
below. This evidence validates the workflow helper, not integration runtime
behaviour. No issue fix or target installation is part of setup.

On 19 October 2026, live discovery retrieved all 23 open issues, complete issue
bodies/comments, labels, native dependency collections, all-state PRs and fork
branches. It resolved `Wiggi26/owlet` with ADMIN access. The three existing PRs
(#1, #2 and #26) were merged; none was open. Initial repository labels were
reused unchanged and the six workflow labels above were added. All 23 issues
received `audit`: eight were marked ready (#3, #4, #6, #7, #9, #10, #16, #18)
and fifteen dependency-blocked. No issue was claimed, fixed or closed.

Twenty offline helper scenarios passed using the live snapshot plus synthetic
variations: batch limits one/two/three; no-plan deferral; source/test overlaps;
open textual/native blockers; draft PR references by number, URL and finding ID;
existing issue branches; closed-unmerged prerequisites; merged-but-unreconciled
prerequisites; a merged `Refs` PR with reconciled audit evidence; pending manual
acceptance; missing criteria/dependencies; wildcard scope; unsupported model;
and incomplete/wrong-repository snapshot rejection. These exercise workflow
decisions and do not run the Home Assistant test suite.

A reviewed touch-plan replay proposed #3 (OWL-001/002 only), #10 (OWL-013 only)
and #7 (retained-library contract tests), in priority/roadmap order. #4 and #6
were deferred because their coordinator/setup test paths overlap #3. Each
proposed scope preserves the remaining grouped findings. This is a dated
proposal, not a fixed next batch or an assignment: an implementation invocation
must refresh evidence, acquire the exclusive claim and reduce concurrency if
actual investigation requires shared fixture or semantic changes.

GPT-6 Luna independently exercised a read-only skill invocation and proposed a
single-item batch; GPT-6.1 Sol reviewed the setup for selection, claim, isolation
and completion risks. No blocking findings remained after tightening comment
pagination and model-name validation. Skill frontmatter validation, TOML parsing,
Ruff 0.17.1 lint/format of the helper, local Markdown path checks, scope/privacy
review and whitespace validation passed. The helper uses Python 3.12.14; its
standard-library implementation does not certify integration Python support.
Existing Actions results for the setup PR remain authoritative for hosted CI;
no new local Home Assistant, hassfest/HACS container or live hardware run is
claimed here. Runtime probes and strict xfails retain their documented status.

## Codex documentation

Checked 19 October 2026. The skill format and repository location follow
[Build skills](https://learn.chatgpt.com/docs/build-skills). Project settings and
role files follow [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
and [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Model routing uses [the current model names and access guidance](https://learn.chatgpt.com/docs/models).
The configuration sets agent defaults/cap only; it does not change the user's
coordinator model, credentials, approval policy or sandbox permissions.
