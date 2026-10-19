# Owlet issue batches

The [skill](../.agents/skills/owlet-issue-sprint/SKILL.md) runs one batch under
[AGENTS.md](../AGENTS.md), the [audit](AUDIT.md), [roadmap](ROADMAP.md) and
[testing contract](TESTING.md). Workflow setup does not authorise backlog fixes.

## Run from Codex desktop

Open this project with the setup changes and review/trust its configuration.
Use the same prompt for each batch:

```text
Use $owlet-issue-sprint to implement the next safe remediation batch.
```

For a preview, replace the instruction with `perform a read-only dry run`.
After merges, use `reconcile merged fixes and verification evidence`.
A bare invocation defaults to a dry run. Restart Codex if the skill is missing.

Project configuration defaults to GPT-6 Luna with **high** reasoning and caps
spawned agents at three. Complex work and high-risk review use the Sol roles;
the coordinator model stays user-selected. Availability depends on the account
and client. If delegation/model routing is unavailable, use fewer capable
workers or defer work; never silently downgrade complex tasks to Luna.

## Discovery and touch plans

Requirements: authenticated GitHub CLI, Git and Python 3.12+. From the repo root:

```text
python .agents/skills/owlet-issue-sprint/scripts/discover.py --save .cache/owlet-sprints/backlog.json
```

The helper only reads GitHub. CLI lists paginate up to 10,000 and abort at the
cap; REST collections explicitly paginate. Repository commands select the fork;
`gh api`, which lacks `--repo`, uses literal `repos/Wiggi26/owlet/...` endpoints.
Failed/incomplete discovery produces no usable assignment plan.

Read all open issue bodies/comments, audit entries, dependencies and existing
work. Create a fresh coordinator-reviewed `.cache/owlet-sprints/touch-plan.json`:

```json
{
  "repository": "Wiggi26/owlet",
  "issues": {
    "3": {
      "scope": "OWL-001 only: options constructor",
      "model": "gpt-6-luna",
      "paths": ["custom_components/owlet/config_flow.py", "tests/test_config_flow.py"]
    }
  }
}
```

This illustrates the format, not a fixed assignment. Include every intended
edit, including fixtures; use `*` for unknown scope to prevent parallelism.

```text
python .agents/skills/owlet-issue-sprint/scripts/discover.py --snapshot .cache/owlet-sprints/backlog.json --plan .cache/owlet-sprints/touch-plan.json --limit 3
```

The proposal ranks priority/roadmap order and defers known existing work,
unverified prerequisites, busy/manual-test states and overlapping paths.
Prerequisites require merged evidence and reconciled audit status, not closure
alone. The coordinator must review arbitrary branch/PR names, intersecting globs,
semantic conflicts and narrow prerequisites within partially completed issues.
Replay does not claim work; refresh live discovery after acquiring the lock.
Keep public snapshots/assignments under ignored `.cache/`; never store private
account data, readings or credentials as workflow artifacts.

## Labels

Preserve human labels and reuse existing definitions. Verify fork owner/name
and write access before every GitHub write, including label changes.

| Label | Meaning |
| --- | --- |
| `audit` | Stable audit-backlog marker. |
| `agent:ready` | Unclaimed scope is eligible, subject to live review. |
| `agent:in-progress` | Coordinator recorded an active assignment. |
| `agent:blocked` | Named prerequisite, evidence gap or failed check prevents work. |
| `agent:needs-review` | PR/evidence awaits review; issue remains open. |
| `agent:needs-manual-test` | Additional flag for outstanding owner-run acceptance. |

Use one ready/in-progress/blocked/needs-review state plus the optional manual
flag. Explain changed blockers/transitions without repeating unchanged comments.
After full merged verification, close/reconcile and remove obsolete agent flags;
otherwise keep the issue open with its remaining scope.

## Exclusive coordinator claim

1. Verify `Wiggi26/owlet` owner/name, write access and current main SHA. Create
   `refs/heads/codex/issue-sprint-lock` at that SHA using GitHub's **create-ref**
   operation: `gh api --hostname github.com --method POST repos/Wiggi26/owlet/git/refs`
   with `ref` and `sha` fields. Never update an existing lock. Existing ref/422
   stops dispatch; labels alone cannot prevent concurrent claims.
2. Refresh discovery. Record UTC batch ID, coordinator session, base commit,
   issue/OWL scope, acceptance criteria, agent/model, absolute worktree/branch,
   allowed paths and checks in an ignored assignment record. Publish concise
   assignments in selected issues, set in-progress, then dispatch. Failed claim
   writes prevent dispatch. Workers never independently select or claim work.
3. Give each independent issue PR a separate top-level worktree from fork main.
   Threads share files; use explicit working directories. Workers edit/test only
   their assigned scope; coordinator serialises commits and all GitHub writes.
   Shared-worktree edits must be disjoint. Replan any newly discovered overlap.
4. After all workers stop and durable issue/PR handoffs exist, reverify access,
   lock SHA and ownership, then delete only that lock ref. Interrupted locks have
   no automatic expiry: inspect owner, agents, worktrees and handoffs before
   explicitly approved recovery. Never auto-steal a claim or delete issue branches.

Dry runs do not create locks or change labels. Use `Refs #N`, avoid auto-close
keywords and verify fork push URL and both PR repositories before delivery.
Attach PRs to the Codex chat; inspect CI on the latest head. Shared audit/roadmap
updates wait for merged evidence in one later documentation change.

## Verification record

On 19 October 2026, setup discovery retrieved all 23 open issues and their
comments/dependencies, labels, branches and all-state PRs. Existing PRs #1, #2
and #26 were merged. Six workflow labels were added: all 23 issues received
`audit`, eight were ready and fifteen dependency-blocked; none was claimed or closed.

Twenty helper scenarios passed, covering batch limits, overlap, duplicates,
dependency/merge evidence, manual gates and invalid inputs. A touch-plan replay
proposed scoped work on #3, #10 and #7; this dated proposal must be revalidated.
Luna independently exercised the dry run and Sol reviewed the setup. Skill/TOML,
Ruff, path/privacy and whitespace checks passed. All six hosted jobs passed for
the initial setup commit in [CI run 39217260789](https://github.com/Wiggi26/owlet/actions/runs/39217260789).
This does not resolve runtime findings or certify live hardware/cloud behaviour.

Format/configuration references, checked 19 October 2026:
[skills](https://learn.chatgpt.com/docs/build-skills),
[configuration](https://learn.chatgpt.com/docs/config-file/config-reference),
[subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) and
[models](https://learn.chatgpt.com/docs/models).
