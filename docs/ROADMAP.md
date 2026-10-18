# Owlet remediation roadmap

Reviewed **18 October 2026**, against fork `main` at `197bf4e`. This is a proposed implementation sequence for review, not authorisation to implement fixes. The [audit register](AUDIT.md#remediation-register) is the finding/status source; linked fork issues contain detailed evidence, root cause, acceptance criteria, tests, manual checks, dependencies and complexity. All issue/PR work belongs in `Wiggi26/owlet`; upstream is reference-only.

## Baseline and decision rules

[HACS packaging PR #1](https://github.com/Wiggi26/owlet/pull/1) and [CI PR #2](https://github.com/Wiggi26/owlet/pull/2) are merged. Source-directory installation, fork metadata, synthetic JSON fixtures and the offline CI harness are established. Do not recreate ZIP/release deployment infrastructure. Current source, licence/attribution and `owlet` config/entity identities must be preserved during later fixes.

Both reviewed profiles (Core/Python 2025.12.4/3.13.2 and 2026.10.2/3.14.2) execute 56 passes and seven strict expected failures, with 97.53% combined coverage. [TESTING.md](TESTING.md) explains the exact locked environments and limits. These probes do not yet establish a supported version range. Keep `pyowletapi==2025.4.1` until an explicitly reviewed contract/dependency change is justified.

The original roadmap's “PR 1/2/3” were conceptual stages, not GitHub PR numbers. The merged infrastructure is GitHub PR #2; the seven remaining expected failures map to stable findings below. New implementation PRs must cite those IDs rather than treating the old stage numbers as issue ownership.

## Critical blockers

No Critical finding is established. No active credential compromise, destructive Core-wide failure or newly added alarm control is evidenced by this review. This does not certify the integration as safe or medically reliable. It remains supplemental to the official Owlet app/base/alarm system.

If new evidence establishes severe compromise or destructive behaviour, re-triage immediately using redacted evidence. Credential rotation/history rewriting remains a separate authorised action. Do not manufacture urgency from an unverified hypothesis.

## High-priority installation, compatibility and authentication fixes

| Order | Proposed small PR | Findings / fork issue | Prerequisites / completion evidence |
| --- | --- | --- | --- |
| 1 | Repair options construction and absent polling defaults | OWL-001 / OWL-002; [#3](https://github.com/Wiggi26/owlet/issues/3) | Existing harness. Options and legacy-entry setup pass on both profiles; five-second default/minimum retained. |
| 2 | Apply saved polling options and clean up listeners | OWL-003; [#3](https://github.com/Wiggi26/owlet/issues/3) | Step 1. Two-sock reload/update preserves data, options and registry identities. |
| 3 | Restore polling-triggered reauthentication | OWL-004; [#4](https://github.com/Wiggi26/owlet/issues/4) | Existing harness; may proceed beside options. Replace the exact auth xfail with entry-linked recovery. |
| 4 | Validate supported discovery and classify flow errors | OWL-005 / OWL-006; [#5](https://github.com/Wiggi26/owlet/issues/5) | Step 3 for reauth. Initial/reauth/options error and translation-key contracts pass; no unusable empty-account entries. |
| 5 | Remove identity/unsafe exception details from failures | OWL-007; [#6](https://github.com/Wiggi26/owlet/issues/6) | Can proceed independently near the start. Synthetic nested log-redaction tests preserve useful categories. |
| 6 | Lock down retained-library HTTP/normalisation contracts | OWL-017; [#7](https://github.com/Wiggi26/owlet/issues/7) | Test-only preflight before cloud changes; reviewed imports, exceptions, activation/request counts and command results. |
| 7a | Add concurrent/partial token and real storage-reload regressions | OWL-008; [#8](https://github.com/Wiggi26/owlet/issues/8) | Auth recovery and library contracts. Use controlled task events and synthetic persisted entries. |
| 7b | Repair only demonstrated token concurrency/persistence defects | OWL-008; [#8](https://github.com/Wiggi26/owlet/issues/8) | Evidence from 7a. Preserve complete token sets, region, options and identities; no second cloud client. |

Options/API compatibility comes early because it directly blocks configuration, not because all Home Assistant API modernisation is urgent. The optional typed-runtime refactor is Low priority and comes later.

## Reliability and data accuracy fixes

| Order | Proposed small PR | Findings / fork issue | Prerequisites / completion evidence |
| --- | --- | --- | --- |
| 8 | Preserve unknown/new sleep codes consistently | OWL-013; [#10](https://github.com/Wiggi26/owlet/issues/10) | Independent small correction. Remove the specific sleep xfail and cover unfamiliar codes in both platforms. |
| 9 | Reject protocol-invalid numeric values | OWL-012; [#10](https://github.com/Wiggi26/owlet/issues/10) | Separate from sleep mapping. Sentinel/null/string/non-finite/boundary and recovery tests; no medical thresholds, smoothing or clamping. |
| 10 | Make missing-property getters robust | OWL-014; [#9](https://github.com/Wiggi26/owlet/issues/9) | Independent of freshness policy. Missing measurement/charging/control/alert fields cannot break unrelated entities. |
| 11a | Establish source timestamp/flag contracts and preserve UTC | OWL-011 / OWL-015; [#11](https://github.com/Wiggi26/owlet/issues/11) | Library contracts and step 10. Evidence for old/missing/malformed/future timestamps, clock skew and charging flags. |
| 11b | Apply the reviewed freshness/availability policy | OWL-011 / OWL-015; [#11](https://github.com/Wiggi26/owlet/issues/11) | 11a's evidence. Remove stale-data xfail; expose uncertainty when freshness cannot be established. Equal values alone never imply staleness. |
| 12 | Classify HTTP failures and bound account backoff/request work | OWL-009 / OWL-010; [#12](https://github.com/Wiggi26/owlet/issues/12) | Library and token contracts. Explicit 401/403/429/5xx, Retry-After, timeout/cancellation, request-count and recovery evidence. |
| 13 | Cover failed setup/cancellation/unload before lifecycle fixes | OWL-041; [#13](https://github.com/Wiggi26/owlet/issues/13) | Options listener work. Demonstrate cleanup on two-sock partial failure; never close HA's shared session. |
| 14 | Establish supported Core/Python and advisory policy | OWL-024 / OWL-030; [#20](https://github.com/Wiggi26/owlet/issues/20) | Configuration/auth fixes; review all remaining High limitations before making support claims. Each advertised pair matches CI and has an explicit advisory result/scope. |

Freshness has high impact but needs protocol evidence; it must not be “fixed” with an invented age cutoff. Low-risk sleep, numeric and getter fixes can progress while that evidence is established. HTTP resilience follows contract/concurrency tests to avoid changing several uncertain behaviours together.

### Existing expected failures

| Test | Finding | Issue |
| --- | --- | --- |
| `test_options_flow` | OWL-001 | [#3](https://github.com/Wiggi26/owlet/issues/3) |
| `test_saved_interval_applies` | OWL-003 | [#3](https://github.com/Wiggi26/owlet/issues/3) |
| `test_coordinator_auth_error` | OWL-004 | [#4](https://github.com/Wiggi26/owlet/issues/4) |
| `test_old_source_measurement_unavailable` | OWL-011 | [#11](https://github.com/Wiggi26/owlet/issues/11) |
| `test_oxygen_sentinel_unavailable` | OWL-012 | [#10](https://github.com/Wiggi26/owlet/issues/10) |
| `test_unknown_sleep_not_awake` | OWL-013 | [#10](https://github.com/Wiggi26/owlet/issues/10) |
| `test_missing_measurement_is_unknown` | OWL-014 | [#9](https://github.com/Wiggi26/owlet/issues/9) |

Each fix must make the intended test pass, remove only its matching strict marker, add relevant edge/recovery tests and update merged evidence. Do not skip tests or reinterpret an expected failure as compatibility.

## Medium-priority improvements

Each row is a separate PR or an investigation followed by a narrowly justified fix. They are not a single combined “cleanup” PR.

| Work | Finding / issue | Dependency / acceptance focus |
| --- | --- | --- |
| Device arrival, optional capabilities and discovery metadata | OWL-016; [#14](https://github.com/Wiggi26/owlet/issues/14) | Missing-field and cloud lifecycle work; bounded discovery/reload policy, no duplicate registry entities. |
| Existing base-station switch capability/result handling | OWL-018; [#15](https://github.com/Wiggi26/owlet/issues/15) | Missing-field/library contracts; failed commands are visible, identity retained. Mocked commands only; physical/alarm behaviour needs separate approval. |
| Truthful hardware/MAC metadata | OWL-019; [#16](https://github.com/Wiggi26/owlet/issues/16) | Can proceed independently with registry tests. Omit invented facts/invalid connections; avoid casual renaming. |
| Allowlisted diagnostics, repair and retention guidance | OWL-020 / OWL-021; [#17](https://github.com/Wiggi26/owlet/issues/17) | Privacy and freshness semantics first; exact synthetic output allowlist, no readings/config entries in exports, no changes to recorder settings. |
| Charging battery spike investigation | OWL-022; [#18](https://github.com/Wiggi26/owlet/issues/18) | No hard prerequisite. Replay synthetic transitions and establish cause before filtering; report remains unverified. |
| Region-aware account identity | OWL-023; [#19](https://github.com/Wiggi26/owlet/issues/19) | Flow/token stability first; separately reviewed old-entry migration/rollback with stable entity bindings. Do not copy upstream PR #30 wholesale. |

## Low-priority enhancements

| Work | Finding / issue | Gate |
| --- | --- | --- |
| Ukrainian localisation and remaining copy | OWL-027; [#23](https://github.com/Wiggi26/owlet/issues/23) | Functional flow keys first; fluent review and no speculative French encoding rewrite or entity-key churn. |
| Typed runtime ownership | OWL-028; [#24](https://github.com/Wiggi26/owlet/issues/24) | Token/lifecycle stability; document the benefit, reuse freshness work and keep the coordinator/library architecture. |
| Optional dashboard example | OWL-029; [#25](https://github.com/Wiggi26/owlet/issues/25) | Correct values/freshness/availability, reviewed switch semantics and diagnostics first. Synthetic-only mobile/tablet/theme/accessibility review; no mandatory new card/client. |

Central brand fallback and deferred camera/prediction/recovery/alarm-control features retain existing scope decisions (OWL-038 / OWL-039). They are not release-blocking defects and do not justify new implementation work.

## Release readiness requirements

Release readiness is an acceptance gate, not permission to publish.

1. Close or explicitly review every applicable High item using merged PRs and exact verification evidence. No strict expected failure may be called a resolved defect; owner acceptance of a remaining risk must be explicit.
2. Publish a factual support policy only for tested Core/Python profiles; reconcile the historical advisory gap. Run pytest with real sockets blocked, Ruff, hassfest, HACS, dependency/security checks and whitespace validation. Keep all six CI jobs mandatory for changes and avoid scheduled runs.
3. Complete [Dream/European/target acceptance (#21)](https://github.com/Wiggi26/owlet/issues/21) (OWL-025) after correctness/auth/reliability prerequisites. This is a separately approved, owner-run check on the target environment, not direct HA/Proxmox access. Record only versions, anonymous counts and pass/fail categories; do not disrupt official monitoring or publish household data.
4. Complete [candidate source/version/install checks (#22)](https://github.com/Wiggi26/owlet/issues/22) (OWL-026). Use `YYYY.M.P`, an exact future tag matching manifest and tested commit, source-directory HACS extraction with translations/LICENSE/NOTICE, dependency equality and no unintended package files. Do not move or repair upstream tags/assets.
5. Verify existing-install upgrade/restart and a documented rollback, retaining config entry IDs/data/options/region, entity IDs/unique IDs, registry associations, disabled states and user customisations. Test old-entry storage migrations where applicable, not just a same-process unload.
6. Present the candidate commit, check links, package inspection, supported versions, unresolved cloud/firmware limitations and rollback evidence for a separate owner decision. Do not publish a release, deploy, merge or change official monitoring as part of this plan.

## Maintaining the plan

All implementation work needs a new explicit instruction. Use a separate worktree and short `codex/` branch per focused change. Before GitHub writes, verify the fork's owner/name and access; check existing issues, use explicit repository arguments and stop if fork access fails. Link upstream reports only as historical evidence.

Consult the audit/roadmap before each change. Reference stable IDs and fork issues in PRs, then update the register, issue and this sequence after merge with exact verification and remaining risk. A new finding must distinguish source-confirmed behaviour, synthetic reproduction, upstream report and unverified hypothesis. Keep detailed acceptance in the existing issues instead of duplicating them across new tickets.
