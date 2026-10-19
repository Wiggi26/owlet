# Owlet maintenance audit

Original audit and re-triage date: **18 October 2026**. The register below is the current status; the original source audit and earlier follow-ups are retained afterwards as dated evidence. Statements about absent CI, ZIP packaging or matching upstream branches in those snapshots are historical.

## Remediation review

Reviewed fork `main` at [`197bf4e`](https://github.com/Wiggi26/owlet/commit/197bf4e2b316d5f8b7791b179371b0c887153f4c), after merged [packaging PR #1][packaging-pr] and [CI PR #2][ci-pr]. The fork issue listing was checked in all states, including pagination, before creating this backlog; it contained only those two PRs. Upstream's 31 issue/PR records were rechecked, with relevant discussion on #2, #9, #27, #29, #30 and #31. Upstream is reference-only; every new issue is in the fork.

**41 findings: 30 Open (13 High, 14 Medium, 3 Low), 9 Resolved, 2 Accepted Risk. No Critical finding is established.** The 30 open findings are grouped into [22 open fork issues](https://github.com/Wiggi26/owlet/issues?q=is%3Aissue+is%3Aopen). Reconciled on **19 October 2026** against fork `main` at `2f15566`. Open includes merged fixes awaiting mandatory manual acceptance or remaining scope; only OWL-017 meets its complete closure gate. Dependencies, likely root cause, solution, acceptance criteria, automated/manual tests and Small/Medium/Large complexity are recorded in each issue. [ROADMAP.md](ROADMAP.md) sequences small PRs; [TESTING.md](TESTING.md) describes the existing harness.

Severity describes impact; priority describes order. **Critical** requires established severe compromise, destructive failure or similarly urgent impact; none is evidenced here. **High / P1** covers setup/recovery failure, misleading measurements or material privacy/availability risk. **Medium / P2** covers bounded reliability, metadata, maintenance and privacy improvements. **Low / P3** covers optional enhancements/copy. OWL-026 is Medium but P1 **before release**. Validation gaps receive impact severity without being called observed runtime defects.

Status vocabulary is Open, In Progress, Resolved, Accepted Risk or Blocked. In Progress requires actual authorised work; Blocked names its prerequisite; Resolved requires merged/current-tree evidence and applicable verification. An issue closure, expected failure or metadata pass alone is insufficient. Accepted Risk below records existing source-layout/non-goal decisions, not acceptance of unresolved measurement or credential risks. Revisit those decisions if requirements change.

## Remediation register

Related PR records merged work, including partial fixes; it does not alone mean Resolved. Pending implementation PRs remain tracked on the issue. PR #2 supplies baseline evidence for open regression cases, not their resolution. Evidence links for source/tests are in the corresponding issue; current source was re-reviewed without changing it.

| Finding ID | Finding / classification | Severity / priority | Status | Fork issue | Related PR | Verification evidence | Outstanding risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="owl-001"></a>OWL-001 | Options constructor uses a read-only property (Confirmed defect) | High / P1 | Open | [#3](https://github.com/Wiggi26/owlet/issues/3) | [PR #28](https://github.com/Wiggi26/owlet/pull/28) | Supported options property; open/save/reopen regressions pass on both profiles; matching xfail removed. | Shared synthetic options UI/restart acceptance remains for #3. |
| <a id="owl-002"></a>OWL-002 | Missing polling option has no fallback (Confirmed source defect) | High / P1 | Open | [#3](https://github.com/Wiggi26/owlet/issues/3) | [PR #28](https://github.com/Wiggi26/owlet/pull/28) | Missing scan_interval uses five seconds; old-entry data/options preservation passes on both profiles. | Mandatory synthetic options/restart acceptance remains; no reinstall or identity migration. |
| <a id="owl-003"></a>OWL-003 | Saved polling changes do not affect running coordinators (Confirmed defect) | Medium / P2 | Open | [#3](https://github.com/Wiggi26/owlet/issues/3) | [PR #37](https://github.com/Wiggi26/owlet/pull/37) | Saved interval changes apply to running coordinators; matching regression passes on both profiles. | Mandatory synthetic options UI/restart/effective-interval/binding acceptance remains (#3: needs-manual-test). |
| <a id="owl-004"></a>OWL-004 | Polling authentication masks reauth with an email lookup (Confirmed defect) | High / P1 | Open | [#4](https://github.com/Wiggi26/owlet/issues/4) | [PR #33](https://github.com/Wiggi26/owlet/pull/33) | Entry-linked polling reauth and both-region/two-sock recovery pass; matching xfail removed. | Mandatory owner-run synthetic prompt and binding acceptance remains (#4: needs-manual-test). |
| <a id="owl-005"></a>OWL-005 | Setup discovery and failure classification are incomplete (Confirmed defect) | High / P1 | Open | [#5](https://github.com/Wiggi26/owlet/issues/5) | — | Authentication-only initial validation; setup/discovery and flow tests confirm generic/empty error handling. | Empty accounts and transient failures produce unusable setup or unclear recovery. |
| <a id="owl-006"></a>OWL-006 | Flow errors and option translation keys are inconsistent (Confirmed defect) | Medium / P2 | Open | [#5](https://github.com/Wiggi26/owlet/issues/5) | — | No `no_devices` translation; all option schemas label `pollinterval`/minimum 10 instead of `scan_interval`/minimum 5. | no_devices is untranslated; scan_interval is labelled under pollinterval/minimum 10. |
| <a id="owl-007"></a>OWL-007 | Errors expose account identity and unreviewed exception detail (Security concern) | High / P1 | Open | [#6](https://github.com/Wiggi26/owlet/issues/6) | [PR #39](https://github.com/Wiggi26/owlet/pull/39) | Integration-owned error/log paths no longer expose account identity or exception details; both profiles pass. | Blocked on unresolved Core-generated entry-title identity and switch-command privacy tracked by #15; no title migration is included. |
| <a id="owl-008"></a>OWL-008 | Concurrent/partial refresh and storage restart are unproven (Validation gap; suspected race) | High / P1 | Open | [#8](https://github.com/Wiggi26/owlet/issues/8) | — | Shared client and token merges; unload/re-setup tested, concurrency/partial exchange/storage restart not tested. | Rotation/unload tests exist; long-lived concurrent correctness is unverified. |
| <a id="owl-009"></a>OWL-009 | Transient HTTP failures can trigger auth refresh without bounded backoff (Confirmed source behaviour) | High / P1 | Open | [#12](https://github.com/Wiggi26/owlet/issues/12) | — | Pinned-library validation reauthenticates on any non-200/201; no 429/Retry-After classification or account backoff. | Actual current-service status/limit behaviour remains unverified. |
| <a id="owl-010"></a>OWL-010 | Validation and activation amplify cloud request counts (Confirmed source behaviour) | Medium / P2 | Open | [#12](https://github.com/Wiggi26/owlet/issues/12) | — | Library activation + properties + validation contract, recorded in original audit; five-second minimum retained. | At least four requests per sock per poll; activation effects/rate limits unknown. |
| <a id="owl-011"></a>OWL-011 | Successful polls accept stale or ambiguous source measurements (Confirmed defect) | High / P1 | Open | [#11](https://github.com/Wiggi26/owlet/issues/11) | — | `test_old_source_measurement_unavailable` strict xfail; timezone information is lost by library formatting. | Old readings can look current; cloud timestamp advances cannot prove a new device sample. |
| <a id="owl-012"></a>OWL-012 | Numeric measurements lack a complete validity policy (Confirmed defect) | High / P1 | Open | [#10](https://github.com/Wiggi26/owlet/issues/10) | [PR #38](https://github.com/Wiggi26/owlet/pull/38) | Normalized numeric validity handling merged; matching normalized-value regression passes on both profiles. | Raw parser coercion/failure isolation remains under #9; synthetic UI acceptance remains. No complete raw-payload validity policy is established. |
| <a id="owl-013"></a>OWL-013 | Unknown sleep becomes awake or raises on a new code (Confirmed defect) | High / P1 | Open | [#10](https://github.com/Wiggi26/owlet/issues/10) | [PR #29](https://github.com/Wiggi26/owlet/pull/29) | Known sleep meanings preserved; unknown/new normalized codes remain unknown; matching regression passes with its xfail removed. | Synthetic UI acceptance and grouped OWL-012 raw-value work remain open. |
| <a id="owl-014"></a>OWL-014 | Disappearing properties can raise from entity getters (Confirmed defect) | High / P1 | Open | [#9](https://github.com/Wiggi26/owlet/issues/9) | [PR #34](https://github.com/Wiggi26/owlet/pull/34) | Normalized getters tolerate missing/malformed values; two-sock recovery and IDs pass; matching xfail removed. | Raw malformed numbers/flags may still fail or be collapsed by the parser; synthetic UI acceptance remains. |
| <a id="owl-015"></a>OWL-015 | Alert availability during charging lacks freshness/reset evidence (Confirmed policy gap) | Medium / P2 | Open | [#11](https://github.com/Wiggi26/owlet/issues/11) | — | Alert descriptions remain available while charging; upstream retained-flag discussion is historical evidence, not a verified current alarm contract. | Retained flags may be read as current official monitoring. |
| <a id="owl-016"></a>OWL-016 | Discovery and optional capabilities are static after setup (Enhancement gap) | Medium / P2 | Open | [#14](https://github.com/Wiggi26/owlet/issues/14) | — | Discovery and platform capability filters execute at setup only; normal initial two-sock creation already passes. | New/returning devices or fields may require reload; careless reconciliation risks duplicates. |
| <a id="owl-017"></a>OWL-017 | Full pinned-library contracts and upgrade compatibility need review (Technical debt) | Medium / P2 | Resolved | [#7](https://github.com/Wiggi26/owlet/issues/7) | [PR #30](https://github.com/Wiggi26/owlet/pull/30) | Actual HTTP/session contracts, metadata, imports, hashes and privacy reviewed; exact 2025.4.1 pin retained; #7 closed. | Token persistence, HTTP/backoff, command semantics and live compatibility remain #8/#12/#15/#21; successor pins need separate review. |
| <a id="owl-018"></a>OWL-018 | Switch capability and command results are not checked (Confirmed defect/design gap) | Medium / P2 | Open | [#15](https://github.com/Wiggi26/owlet/issues/15) | — | Switch added unconditionally; command result discarded, state updated by later polling. | Existing control success/state can be misunderstood. |
| <a id="owl-019"></a>OWL-019 | Device metadata fabricates hardware and accepts invalid connections (Confirmed defect) | Medium / P2 | Open | [#16](https://github.com/Wiggi26/owlet/issues/16) | [PR #35](https://github.com/Wiggi26/owlet/pull/35) | Invented hardware and invalid new MAC connections omitted; V2/V3 registry/customisation reload checks pass. | Mandatory device-page acceptance remains; legacy stored facts/placeholder merges are not automatically repaired. |
| <a id="owl-020"></a>OWL-020 | Allowlisted diagnostics and repair/freshness guidance are absent (Enhancement gap) | Medium / P2 | Open | [#17](https://github.com/Wiggi26/owlet/issues/17) | — | No `diagnostics.py`, measurement-age entity or structured repair guidance in the current inventory. | Troubleshooting can invite unsafe sharing; age metadata depends on trustworthy source semantics. |
| <a id="owl-021"></a>OWL-021 | Recorder/statistics/backup retention guidance is missing (Privacy documentation gap) | Medium / P2 | Open | [#17](https://github.com/Wiggi26/owlet/issues/17) | — | Physiological sensors have measurement state classes; recorder/backup minimisation guidance is absent. | User-owned HA storage can retain sensitive data; no settings changes authorised. |
| <a id="owl-022"></a>OWL-022 | Charging battery spike is reported but not reproduced (Reported defect) | Medium / P2 | Open | [#18](https://github.com/Wiggi26/owlet/issues/18) | — | Upstream #2/reply report a transition spike; no reproducible integration conversion defect established. | Root cause is unknown; filtering/smoothing is unjustified. |
| <a id="owl-023"></a>OWL-023 | Email-only config identity prevents dual-region setup (Confirmed limitation) | Medium / P2 | Open | [#19](https://github.com/Wiggi26/owlet/issues/19) | — | Config unique ID is lowercased username without region; upstream PR #30 remains unmerged. | Migration can cause duplicates or broken bindings unless tested separately. |
| <a id="owl-024"></a>OWL-024 | A supported Core/Python policy remains undeclared (Compatibility debt) | High / P1 | Open | [#20](https://github.com/Wiggi26/owlet/issues/20) | — | Two exact CI probes with remaining runtime/manual acceptance gaps; no declared supported floor/range. | Two tested probes with known gaps do not establish an unrestricted support range. |
| <a id="owl-025"></a>OWL-025 | Current Dream/European/firmware acceptance is unverified (Validation gap) | High / P1 | Open | [#21](https://github.com/Wiggi26/owlet/issues/21) | — | No live target acceptance in audit or CI; library region support cannot prove Dream/firmware behaviour. | No live incompatibility proved; target-operation/release claims remain unverified. |
| <a id="owl-026"></a>OWL-026 | Future candidate source/version/install/rollback gate is incomplete (Release-process debt) | Medium / P1 before release | Open | [#22](https://github.com/Wiggi26/owlet/issues/22) | — | Upstream tag/ZIP hash/pin comparison; fork extraction passed but future candidate/version/live rollback gate not completed. | Historical upstream tag/ZIP mismatch remains immutable; avoid repeating it in the fork. |
| <a id="owl-027"></a>OWL-027 | Ukrainian localisation and copy need review (Localisation debt) | Low / P3 | Open | [#23](https://github.com/Wiggi26/owlet/issues/23) | — | Ukrainian file contains English text; source copy/labels have established issues; fluent review pending. | English Ukrainian copy and typos remain; entity keys/names require care. |
| <a id="owl-028"></a>OWL-028 | Typed runtime ownership is optional modernisation (Technical debt enhancement) | Low / P3 | Open | [#24](https://github.com/Wiggi26/owlet/issues/24) | — | Current `hass.data`/mutable Sock and `None` update result; official runtime-data guidance is a recommendation. | hass.data/None coordinator return are not demonstrated API failures; reuse freshness work. |
| <a id="owl-029"></a>OWL-029 | Optional dashboard examples and rendering acceptance are absent (Enhancement opportunity) | Low / P3 | Open | [#25](https://github.com/Wiggi26/owlet/issues/25) | — | No public example/rendering evidence; upstream movement sensors already exist and are registry-enabled. | Defer until reliable values/freshness; household layout is not public acceptance evidence. |
| <a id="owl-030"></a>OWL-030 | Historical compatibility profile is outside advisory scanning (Confirmed CI coverage gap) | Medium / P2 | Open | [#20](https://github.com/Wiggi26/owlet/issues/20) | — | Dependency job installs/audits only current-Core locked environment, as explicitly documented in TESTING.md. | Current-profile pip-audit success does not cover the historical environment. |
| <a id="owl-031"></a>OWL-031 | HACS requires a missing owlet.zip asset (Packaging defect) | High / P1 | Resolved | — | [PR #1][packaging-pr] | Standard source-directory HACS configuration, validated extraction and metadata checks. | Live install/update acceptance remains OWL-025 / OWL-026. |
| <a id="owl-032"></a>OWL-032 | Repository URLs and installation/update instructions point upstream (Documentation defect) | Medium / P2 | Resolved | — | [PR #1][packaging-pr] | Manifest issue/documentation URLs and factual README/info paths target the fork; original attribution/licence preserved. | Future support claims remain OWL-024; keep upstream links only as reference. |
| <a id="owl-033"></a>OWL-033 | Advertised 2024.1 minimum lacks ConfigFlowResult (Compatibility claim defect) | High / P1 | Resolved | — | [PR #1][packaging-pr] | Unsupported HACS/Core minimum removed; no claim of runtime repair. | Selecting and proving a support floor remains OWL-024. |
| <a id="owl-034"></a>OWL-034 | Inherited tests cannot run as a custom integration (Test-infrastructure defect) | High / P1 | Resolved | — | [PR #2][ci-pr] | Locked custom-component harness, mocked cloud/socket guards, 56 passes + 7 strict xfails on each explicit profile; 97.53% coverage. | Expected failures stay open; coverage gaps map to OWL-008 / OWL-017 / OWL-023 / OWL-024 / OWL-030 / OWL-041. |
| <a id="owl-035"></a>OWL-035 | Fixture contents have undocumented synthetic provenance (Privacy concern) | High / P1 | Resolved | — | [PR #2][ci-pr] | All six JSON filenames retained with wholly synthetic contents and provenance documentation; copy-isolated helpers. | This resolves the current tree, not a history-wide leak certification; no active leak established. |
| <a id="owl-036"></a>OWL-036 | CI uses dated floating actions and a daily schedule (Workflow/security debt) | Medium / P1 | Resolved | — | [PR #2][ci-pr] | SHA-pinned actions, hosted Ubuntu/main push+PR only, read-only token, concurrency/timeouts, Ruff/pytest/hassfest/HACS/zizmor/current pip-audit. | Baseline advisory scope is OWL-030; upstream container wrappers and future revisions still need review. |
| <a id="owl-037"></a>OWL-037 | Historical V2/multiple-sock/oxygen-average/state-class/interval issues (Historical resolved defects) | Medium / P2 | Resolved | — | Upstream fixes; [tests #2][ci-pr] | Current source retains upstream fixes; CI covers V2, two socks, average sentinel bounds, charging and registry identities; schema minimum/default are five seconds. | Retain regressions; this does not resolve fresh/instantaneous values or future firmware. |
| <a id="owl-038"></a>OWL-038 | No local brand icon (Metadata warning) | Low / P3 | Accepted Risk | — | [PR #1][packaging-pr] | HACS passes using the existing central owlet brands assets, with an explicit fallback warning. | Existing source-layout decision accepts the fallback; revisit only if HACS requires local assets. |
| <a id="owl-039"></a>OWL-039 | Camera/prediction/recovery/alarm-control feature requests (Deferred enhancements/non-goals) | Low / P3 | Accepted Risk | — | — | Audit scope and existing maintenance rules explicitly defer these features; no present maintenance defect established. | Existing scope decision only; any later support/safety change requires separate authorisation. No alarm-silencing work. |
| <a id="owl-040"></a>OWL-040 | Suspected French encoding artifacts (Unconfirmed earlier suspicion) | Low / P3 | Resolved | — | — | Current file decodes/parses as UTF-8 JSON, displays French accents, and has zero U+FFFD/common mojibake markers; earlier encoding claim corrected. | Not a complete linguistic review; copy/key issues remain OWL-006 / OWL-027. No speculative encoding fix. |
| <a id="owl-041"></a>OWL-041 | Partial setup/cancellation/unload failure paths lack coverage (Validation gap) | Medium / P2 | Open | [#13](https://github.com/Wiggi26/owlet/issues/13) | — | Normal unload/reload passes; failed concurrent setup/cancellation/partial forwarding not covered. | No task/session leak established; normal reload/unload is already covered. |

### Merged-evidence reconciliation — 19 October 2026

All six required checks passed at each final PR head below. Both exact profiles
were **Core 2025.12.4 / Python 3.13.2** and **Core 2026.10.2 / Python 3.14.2**;
counts are per profile, not totals or current-main counts. Source/metadata/hash
review completes OWL-017 without live access. All other listed issues remain open
for their remaining scope or mandatory manual checks described in the register.

| PR / issue | Merge commit | Final-head CI | Passed / strict xfails / coverage |
| --- | --- | --- | --- |
| [#28](https://github.com/Wiggi26/owlet/pull/28) / #3 | `202d1eae69de124dfc5fdd080eb4407b5e50a1dc` | [88d039c](https://github.com/Wiggi26/owlet/actions/runs/39220891065) | 59 / 6 / 99.38% |
| [#29](https://github.com/Wiggi26/owlet/pull/29) / #10 | `d3980ee50f221fd6e6c7d715bf84b5c01cfbe8d0` | [a6b006b](https://github.com/Wiggi26/owlet/actions/runs/39220929013) | 67 / 6 / 97.60% |
| [#30](https://github.com/Wiggi26/owlet/pull/30) / #7 | `bd3bd2a5216133aac44ecfeb88f8bb8c61becd9d` | [e7a3edd](https://github.com/Wiggi26/owlet/actions/runs/39299321334) | 140 / 7 / 97.53% |
| [#33](https://github.com/Wiggi26/owlet/pull/33) / #4 | `85173c147dc55af27b8ef10f8f8917da88da0eda` | [22e9c24](https://github.com/Wiggi26/owlet/actions/runs/39302371348) | 157 / 4 / 99.40% |
| [#34](https://github.com/Wiggi26/owlet/pull/34) / #9 | `6feada08c145d04ed64ac5c0fdd8d132569ec3a9` | [3ec870e](https://github.com/Wiggi26/owlet/actions/runs/39302979489) | 161 / 4 / 98.44% |
| [#35](https://github.com/Wiggi26/owlet/pull/35) / #16 | `2290b6e78f9522f9cfd6b5cb5d7124faf9999855` | [70d2f19](https://github.com/Wiggi26/owlet/actions/runs/39303545666) | 158 / 5 / 99.43% |
| [#37](https://github.com/Wiggi26/owlet/pull/37) / #3 | `f433772effadc051954cbb73a01877bb15462775` | [6c2f372](https://github.com/Wiggi26/owlet/actions/runs/39305972800) | 173 / 2 / 98.54% |
| [#38](https://github.com/Wiggi26/owlet/pull/38) / #10 | `63f156d76fd31c9ec7180c3d186e26a7033da5fc` | [1d01b7d](https://github.com/Wiggi26/owlet/actions/runs/39306181225) | 211 / 2 / 98.56% |
| [#39](https://github.com/Wiggi26/owlet/pull/39) / #6 | `2f1556652897ab1ec9d504017ef770ba84d363c5` | [ae747b9](https://github.com/Wiggi26/owlet/actions/runs/39309311786) | 268 / 1 / 98.62% |

The combined main [run 39304155274](https://github.com/Wiggi26/owlet/actions/runs/39304155274)
also passed for the earlier `85173c1` state. The three newer final-head runs each
passed all six required checks on both exact profiles. PR #39's final-head suite
has one strict xfail, the stale-source regression; #37/#38 report two each. This
reconciliation adds no runtime, dependency, support-range or live-device claims. No High risk is
accepted by closing the contract-only issue.

### Overlap and coverage decisions

- Options constructor, absent defaults and saved intervals share #3; setup discovery and translated error/option contracts share #5.
- Frozen-reading reports, source-time loss and charging alert freshness share #11. Numeric validation and unknown sleep share #10, with separate small implementation PRs.
- Library contracts (#7) precede concurrency (#8) and HTTP/backoff/request accounting (#12); reports do not prove a refresh race or current rate limit.
- Missing-field recovery (#9) is distinct from adding future devices/capabilities (#14). Historical V2/multiple-sock fixes are preserved rather than re-filed as current failures.
- The unsupported minimum claim is resolved (OWL-033); selecting a supported minimum and auditing its dependencies remain OWL-024 / OWL-030. Current packaging is resolved (OWL-031 / OWL-032); historical tag/ZIP divergence and future release acceptance remain OWL-026.
- French encoding suspicion (OWL-040) was not reproduced in UTF-8/JSON review: accents display correctly, with no replacement/common mojibake markers. Ukrainian English text and functional translation-key/label errors remain separate open items.
- Camera, predicted/derived sleep, recovery-mode/alarm-control features and a rewrite stay deferred by existing scope. No new support or automatic alarm control is proposed.

### Original re-triage verification and remaining uncertainty

The merged-main [CI run 39160237837](https://github.com/Wiggi26/owlet/actions/runs/39160237837) has six successful jobs. The verified pre-merge [run 39159831341](https://github.com/Wiggi26/owlet/actions/runs/39159831341) and local runs report **56 passed, 7 strict expected failures, 97.53% combined coverage** for Core/Python **2025.12.4/3.13.2** and **2026.10.2/3.14.2**. These are probes with known failures, not a full compatibility/support claim. Current-profile pip-audit, Ruff, zizmor, HACS and hassfest passed; historical-profile advisories and full cloud/firmware contracts are not established. HACS's central-brand fallback warning remains explicit.

Planning validation passed: all 41 unique finding IDs/statuses, 31 open-to-issue mappings, 23 complete fork issue records, acyclic linked dependencies, source paths, local Markdown paths/fragments and whitespace. Only AGENTS.md, AUDIT.md and ROADMAP.md change; application/tests/workflows/dependencies are preserved. No new local runtime test execution, live login, target installation, deployment, release or clinical acceptance is claimed. Manual checks in the issues are future owner-run requirements after separate approval; do not request credentials, direct HA/Proxmox access or live captures. The integration remains supplemental to official Owlet monitoring.

[packaging-pr]: https://github.com/Wiggi26/owlet/pull/1
[ci-pr]: https://github.com/Wiggi26/owlet/pull/2

## Historical audit and follow-up snapshots

The following sections preserve earlier evidence and scope statements. The remediation register above supersedes their old status/priority and future-PR numbering; it does not erase unresolved runtime findings.


## Packaging follow-up — 18 October 2026

This follow-up was authorised separately from the original documentation-only audit. The original audit and roadmap were untracked in the earlier audit worktree; they are carried into this packaging PR for traceability. See [PACKAGING.md](PACKAGING.md) for the decision, source references, validation evidence, and limits.

| Finding | Current status / evidence |
| --- | --- |
| Public-fork installation instructions and metadata point upstream | Addressed: current repository links, manifest ownership, installation/upgrade/troubleshooting, and version policy updated. The integration remains named Owlet. Historical upstream attribution and issue/commit evidence remain. |
| Fork requires a missing `owlet.zip` release asset | Addressed in the candidate configuration: ZIP settings removed; HACS's standard single-integration source layout is used. Official validator and archive-extraction results are recorded in PACKAGING.md. No live HACS/HA installation is claimed. |
| Upstream `2025.4.3` tag and uploaded ZIP have different pins | Historical mismatch remains. New fork version `2026.10.0` is reserved, unreleased; future releases must match manifest/tag/source and use the tagged sources. Existing upstream tags/assets were not changed. |
| Advertised HA minimum lacks `ConfigFlowResult` | Incorrect `2024.1` declaration removed; tested support floor remains unresolved. Removing a compatibility claim does not fix runtime behaviour. |
| Brand assets absent from this repository | Clarified: no local assets, but the unchanged `owlet` domain has icon/logo assets in `home-assistant/brands/custom_integrations/owlet`. Official HACS validation passed using that fallback, with a warning about the absent local icon. No new asset submission is needed for this packaging change. |
| Validation workflow age and permissions | Partially addressed: reviewed action references, read-only contents permission, disabled PR comments, timeouts, concurrency, and action-update tracking. Validation runs on pushes and PRs only in `validate.yml`; the daily schedule is removed. Runtime harness, Ruff baseline, and Core/Python matrix remain pending. |
| Runtime options/authentication, stale/invalid values, diagnostics, fixture provenance, dashboard examples | Unresolved and outside this packaging change. No runtime or translation source was changed. |

The PyPI availability, hashes, exception imports, and public method contracts for the retained `pyowletapi==2025.4.1` pin were rechecked. Newer inspected versions still remove required exceptions; this is not a dependency upgrade or a full Core compatibility certification.

## Automated test baseline — 18 October 2026

The inherited test-harness/CI finding is addressed by the offline custom-component suite and locked development environment documented in [TESTING.md](TESTING.md). Core/Python pairs `2025.12.4`/`3.13.2` and `2026.10.2`/`3.14.2` each execute **63 cases: 56 passed, 7 strict expected failures**, with **97.53% combined line/branch coverage**. Both GitHub matrix jobs passed in [run 39158262400](https://github.com/Wiggi26/owlet/actions/runs/39158262400); final-head checks are recorded in the PR.

The six inherited capture-like fixture filenames are retained with entirely synthetic JSON contents and documented provenance; Python helpers apply isolated edge-case overrides. Tests load `custom_components.owlet`, use the real pinned library's normalisation, mock all cloud entry points, prohibit network sockets, and fail on unmocked low-level calls. Ruff lint/format, zizmor, current locked-environment pip-audit, HACS and hassfest passed. Runtime edits are limited to mechanical formatting/import cleanup; manifest, dependency pin, translations, identities and original licence are unchanged.

The seven expected failures confirm the existing options constructor, polling auth key, options-update, stale source measurement, instantaneous oxygen sentinel, unknown sleep and disappearing-property defects. They remain **open**, with specific failure signatures and roadmap PR 2/3 ownership. Passing CI does not establish full runtime compatibility. Concurrent refresh, partial exchanges, process-restart persistence, full HTTP/throttling contracts, timestamp/firmware variants, diagnostics redaction, and actual cross-Core storage migrations still need coverage. The historical baseline's dependencies are not included in the current-environment vulnerability scan.

## Scope, provenance, and limits

The inspected public fork is [Wiggi26/owlet](https://github.com/Wiggi26/owlet), derived from [ryanbdclark/owlet](https://github.com/ryanbdclark/owlet). Both `main` branches resolve to `f8e0067a1e74a523b0bb4b0841b25404a6926ca8`; upstream is archived and the fork is not. The target is a Smart Sock 3 using the Dream app and a European account, with Home Assistant OS on Proxmox. The installed Core, HACS, device firmware, and account behaviour were not inspected.

Inspection covered all 35 tracked files: integration modules and metadata, all translations, tests and six fixtures, the single workflow, HACS configuration, documentation, licence, and Git settings. Git history was fetched, the full commit log and affected-file history reviewed, and relevant compatibility/authentication/entity changes examined. There are 87 commits reachable from `main`, 88 across fetched refs, 24 tags, and 23 upstream releases. The extra historical ref is not a fork implementation change.

The complete upstream issue/PR listing contains 23 standalone issues and eight PRs, numbered #1 through #31. All 81 issue/conversation comments were retrieved; the inline PR-comment collection was empty. Pagination of the issue listing was checked. Issue attachments containing personal screenshots or readings were not downloaded. The fork had no issues/PRs, releases, or Actions runs in the API snapshot. These are dated observations, not claims about future repository state.

Additional evidence: exact PyPI source distributions for `pyowletapi` 2025.4.1, 2025.4.8, and 2025.4.10, checked against PyPI SHA-256 values; dependency Git history; the actual upstream `2025.4.3` release ZIP; current official Home Assistant/HACS guidance; and Core **2026.10.2**, the latest stable release returned by GitHub during this audit. Core 2024.1.0 was also checked for the advertised minimum-version import.

The Baby Monitor project's two dashboard snapshots dated 16 September 2026 were inspected locally for layout, templates, dependencies, and entity bindings. Their contents and household identifiers are intentionally absent from this public document. There was no live Home Assistant access, cloud login, device operation, deployment, release publication, or browser-rendered dashboard test.

**Evidence labels:** **Confirmed** means directly established by inspected source, metadata, archive contents, or an isolated synthetic check. **Reported** means an upstream user/maintainer observation. **Unverified** means it needs a controlled reproduction or live confirmation. Priority P1 means a maintenance/reliability blocker; P2 means a subsequent improvement. This integration remains supplemental to the official Owlet alarm system.

## Summary

| Finding | Evidence | Priority / implication |
| --- | --- | --- |
| Options flow assigns a now read-only `config_entry` property | Confirmed against Core 2026.10.2 | P1: opening integration options is incompatible with current Core |
| Polling auth failure reads `email`; entries store `username` | Confirmed; synthetic execution raises `KeyError('email')` | P1: masks the intended reauthentication exception |
| Successful polls accept old source measurements | Confirmed missing freshness check; real frozen readings separately reported | P1: old values can look current |
| Instantaneous oxygen lacks sentinel/range validation; unknown sleep becomes awake | Confirmed with synthetic input | P1: misleading measurement/state presentation |
| Existing tests are Core-oriented and absent from CI | Confirmed repository inspection | P1: no reproducible runtime regression gate |
| Release tag and uploaded ZIP differ under the same version | Confirmed inspection of both artifacts | P1 release-process defect: installation channel matters |
| Advertised HA minimum does not provide an imported type | Confirmed Core 2024.1.0 source check | P1 compatibility claim needs correction and testing |
| Changed polling options do not update active coordinators | Confirmed source path | P2: change takes effect only after an external reload/restart |
| Diagnostics, public fork instructions, packaging automation, and Owlet dashboard examples are absent | Confirmed inventory | P2 maintenance and usability gaps |

## Architecture and existing strengths

`config_flow.py` obtains credentials transiently and stores region, username, API token, expiry, refresh token, and polling options. Setup creates one shared `OwletAPI` client and a coordinator per discovered sock. Each coordinator mutates its `Sock` object's properties; entities read those properties rather than coordinator data. The coordinator's update method returns `None`, which is a design limitation for future typed snapshots/freshness handling, not by itself a confirmed runtime failure.

The integration already uses asynchronous library calls, Home Assistant's shared aiohttp session, `CoordinatorEntity`, an awaited `async_forward_entry_setups`, and platform unload handling. Credentials are not persisted as a password by the current flows. Entity unique IDs use `<serial>-<property key>`; registry identifiers use `('owlet', serial)`. The merged multiple-device list fix is present. These are useful foundations to preserve, not reasons to replace the integration. See [setup](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/__init__.py) and [entity base](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/entity.py).

## Home Assistant compatibility

**Confirmed, P1:** `OptionsFlowHandler.__init__` assigns `self.config_entry` at [config_flow.py:156](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/config_flow.py#L156). Home Assistant ended that compatibility allowance in 2025.12; Core 2026.10.2 exposes a property without a setter. This concerns options, not proof that every setup path fails. It independently corroborates [issue #27](https://github.com/ryanbdclark/owlet/issues/27). Sources: [official options-flow change](https://developers.home-assistant.io/blog/2024/11/12/options-flow/) and [Core source](https://github.com/home-assistant/core/blob/2026.10.2/homeassistant/config_entries.py).

**Confirmed, P1:** `hacs.json` advertises Home Assistant `2024.1`, but the integration imports `ConfigFlowResult` from `homeassistant.config_entries`; that class is absent from [Core 2024.1.0](https://github.com/home-assistant/core/blob/2024.1.0/homeassistant/config_entries.py). Select and test a support floor before changing the advertised requirement. The audit did not find the exact earliest compatible release.

Runtime storage in `hass.data` can later move to typed `ConfigEntry.runtime_data`; this is recommended modernisation, not a demonstrated removal of `hass.data`. Likewise, current Core accommodates frozen and non-frozen entity descriptions; the existing dataclasses were not classified as broken simply because they are old. The integration's imported configuration/unit constants checked in current Core remain present. See [runtime-data guidance](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/runtime-data/) and [Core entity descriptions](https://github.com/home-assistant/core/blob/2026.10.2/homeassistant/helpers/entity.py).

**Confirmed, P2:** options are saved, but there is no entry update listener, automatic options reload handler, or live interval setter. Setup reads `scan_interval` once. Missing options also yield `None` instead of a default, which would fail construction of `timedelta(seconds=interval)` for such an entry. No evidence establishes that the user's existing entry lacks this option. Preserve its value and provide a tested fallback.

## Dream authentication, Europe, and refresh

The exact pinned library supports `europe` and `world`, with distinct regional SSO, sign-in, and device API endpoints. Password verification and Google refresh-token exchange precede the mini-token/Ayla sign-in path. The integration passes through the selected region and reauthenticates against the existing entry's region/account. A Smart Sock 3 paired in Dream must not automatically be treated as a distinct API model or assumed compatible solely from its retail name. **Unverified:** current Dream account acceptance, European service behaviour, account migration/firmware differences, and long-lived operation on this user's device. Evidence is library implementation, not a successful live login: [pinned package](https://pypi.org/project/pyowletapi/2025.4.1/).

**Confirmed, P1:** [coordinator.py:50–53](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/coordinator.py#L50) catches `OwletAuthenticationError` but interpolates `entry.data[CONF_EMAIL]`. The flows store `CONF_USERNAME`, not `CONF_EMAIL`. An isolated invocation with a synthetic normally shaped entry raises `KeyError` before `ConfigEntryAuthFailed` can be raised. Fix without logging the account identity.

Token dictionaries are merged into entry data during setup, discovery, and polling. Passwords are omitted from saved entry data and the reauth update. However, there are no working tests for concurrent refresh across the shared account client, partial exchange failure, refresh followed by restart, or rotation during validation. Multiple coordinators share the same API token state without an explicit refresh lock. **Unverified:** an actual refresh race or cross-client sign-out; this must not be presented as an observed incident.

The pinned library's `validate_authentication` treats every non-200/201 response as a reason to clear the access token and authenticate again. Its generic request path converts remaining non-success responses to `OwletConnectionError`; it does not distinguish 429 or inspect `Retry-After`. Temporary service failures can therefore enter token-refresh paths. This is **confirmed source behaviour**; which statuses Owlet currently returns is **unverified**. Preserve expiry/rotation semantics while adding bounded, classified handling through the library boundary.

## Dependency versions and release mismatch

| Artifact | Dependency / inspected behaviour |
| --- | --- |
| Fork and upstream `main`, commit `f8e0067` | Integration version `2025.4.3`; exact dependency `pyowletapi==2025.4.1` |
| Upstream tag `2025.4.3`, commit `45e65f3` | Integration version `2025.4.3`; dependency `pyowletapi==2025.4.8` |
| Actual uploaded `2025.4.3/owlet.zip` | Dependency `2025.4.1`; all 13 files match current integration sources after line-ending normalisation |
| PyPI 2025.4.1 | Contains `OwletEmailError` and `OwletPasswordError`, both imported by the integration |
| PyPI 2025.4.8 and 2025.4.10 | Both exception classes removed; existing integration imports are incompatible |

Sources: [main manifest](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/manifest.json), [tag manifest](https://github.com/ryanbdclark/owlet/blob/2025.4.3/custom_components/owlet/manifest.json), [upstream release](https://github.com/ryanbdclark/owlet/releases/tag/2025.4.3), [revert commit](https://github.com/ryanbdclark/owlet/commit/f8e0067a1e74a523b0bb4b0841b25404a6926ca8), and PyPI sources for [2025.4.8](https://pypi.org/project/pyowletapi/2025.4.8/) and [2025.4.10](https://pypi.org/project/pyowletapi/2025.4.10/).

**Confirmed:** a source/tag installation can encounter the removed-exception import error; the inspected ZIP contains the rollback. **Reported:** [issue #29](https://github.com/ryanbdclark/owlet/issues/29) describes the incompatible pin in the latest release. Do not generalise that report to the current uploaded ZIP or claim all HACS installations are broken. The release/tag discrepancy is itself a reproducibility defect.

The newest PyPI version observed was 2025.4.10, uploaded 16 April 2025. All three inspected packages declare Python `>=3.10` and depend on unpinned `aiohttp`; this does not establish compatibility with Core's current Python/aiohttp. Version 2025.4.8 also contains a `print` of discovered device data, absent from 2025.4.1 and 2025.4.10. Avoid upgrading to it for both compatibility and privacy reasons. Any dependency upgrade needs import, exception, normalisation, discovery, refresh, and command contract tests.

Archive SHA-256: `3a92a8eff048bec6ee0d6d41b0aae157c0e2c0806b4a0528125e6d137b943a8e`. PyPI sdist SHA-256 values checked:

```text
2025.4.1  39c32fe5623d8c17eda43e12740ac5296fa60c27475070db69d775b53a1684a5
2025.4.8  66a65d74b851edd7835c887bb0d47625a5396b59d4506df41b45aae63349faf0
2025.4.10 33a21c77adcc04663fcdbf1a0e845f37190512d72f662bc61c4cabeaf3c4b785
```

## Configuration and reauthentication flows

**Confirmed:** first setup lowercases the username for its unique ID, but stores the original account string and region. The unique ID omits region, preventing the same email from configuring both regions. Open [PR #30](https://github.com/ryanbdclark/owlet/pull/30) proposes a version-2 migration. It is not merged. Do not copy it wholesale: its tests retain the inherited Core test imports, and its debug logging includes old/new account-based identifiers. A migration must preserve entry/entity identities and avoid introducing duplicate devices or exposing account names.

Initial configuration validates authentication status but does not discover supported socks before creating an entry. Empty/unsupported-device accounts can therefore pass this step and fail later in setup. `no_devices` is an emitted error key but is missing from `strings.json` and all translations. `cannot_connect` is translated but not selected by an explicit connection-error branch. Reauth handles a password error, but other exceptions only produce a log entry and redisplay the form without an actionable error. These are **confirmed flow/translation gaps**. See [config flow](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/config_flow.py) and [strings](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/strings.json).

Setup maps credential failures to `ConfigEntryAuthFailed` and connection failures to `ConfigEntryNotReady`, which is the right general separation. `OwletDevicesError` instead returns `False` with a generic log message. Improve the no-device explanation without calling it bad credentials. Current reauth is linked through an entry ID; modern `_get_reauth_entry` and update/reload helpers would reduce duplicated state handling. See [Home Assistant reauth helpers](https://developers.home-assistant.io/blog/2024/10/21/reauth-reconfigure-helpers/).

## Async I/O, polling, throttling, and reconnection

There is no synchronous cloud I/O or blocking sleep in the integration source. Setup uses concurrent first refreshes and a shared client, while each sock has a coordinator interval. The default and UI minimum are five seconds. Upstream rejected a one-second minimum in [PR #12](https://github.com/ryanbdclark/owlet/pull/12); that history is not a published Owlet rate-limit guarantee.

**Confirmed:** a normal pinned-library property poll performs an `APP_ACTIVE` POST and a properties GET. Each request first performs a `/devices.json` authentication validation GET. This is at least four HTTP requests per sock per poll in the valid-token steady state, approximately 48 requests per minute at the default interval, before setup, refresh, or commands. The integration is cloud polling and the library also writes activation state; it is not a purely passive GET client. The consequence of activation for current Dream firmware is unverified.

There is no integration-level timeout envelope, account-wide throttling/backoff, or refresh lock. The shared aiohttp session does have its own defaults; the absence of a custom timeout is not proof that requests can wait forever. Coordinator failures normally affect entity availability and subsequent scheduled retries; setup connection failures are retryable. There is no explicit rediscovery loop for devices added after setup, and stored discovery connection metadata is not refreshed on each property poll. Test recovery, cancellation, multi-device isolation, and unload before redesigning scheduling. See [Home Assistant fetching-data guidance](https://developers.home-assistant.io/docs/integration_fetching_data/).

## Physiological data correctness and freshness

**Confirmed, P1:** neither the coordinator nor entity availability checks use source age. Pinned `pyowletapi` parses the V3 `REAL_TIME_VITALS.data_updated_at` field into a timezone-free formatted `last_updated` string, but the integration does not expose or check it. Synthetic input with a deliberately old source timestamp is normalised successfully. An HTTP success therefore cannot establish a new measurement. [Issue #9](https://github.com/ryanbdclark/owlet/issues/9) contains the maintainer's historical explanation that the API may retain measurements and base flags after power loss; [issue #31](https://github.com/ryanbdclark/owlet/issues/31) reports recently frozen heart-rate values. Those real-world causes remain unverified on the target device.

Freshness handling should retain the raw UTC timestamp, distinguish measurement time from poll time, validate timestamp behaviour across repeated values, and handle absent/future timestamps explicitly. A changing HA `last_updated`/`last_reported`, a new successful request, or a constant heart rate is not sufficient proof either way. If source timestamps advance while old values are replayed, timestamp checks alone cannot detect that; document the limitation. Do not invent a universal stale cutoff from the five-second poll interval.

**Confirmed, P1:** only the 10-minute oxygen average has a 0–100 availability check. Instantaneous oxygen and heart rate are passed through, and the library accepts a synthetic instantaneous oxygen sentinel of 255. Missing/null values, non-finite numbers, malformed numeric fields, and firmware-specific validity flags need a documented validation policy. Reject impossible/sentinel values; do not choose medical alarm thresholds or turn invalid values into plausible readings. The historical 255-average fix is already present from [PR #14](https://github.com/ryanbdclark/owlet/pull/14).

**Confirmed, P1:** `OwletAwakeSensor.is_on` treats every sleep code other than 8 and 15 as awake, including code 0, which the ordinary sleep sensor labels unknown. A synthetic code-0 check returns true. The ordinary sleep sensor directly indexes a four-code mapping, so a new code can raise `KeyError`. Unknown and unsupported codes should be unknown, not inferred as awake. See [binary_sensor.py:169](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/binary_sensor.py#L169) and [sensor.py:184](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/sensor.py#L184).

**Reported, unverified cause:** [issue #2](https://github.com/ryanbdclark/owlet/issues/2) describes a momentary charging/battery jump. No evidence justifies smoothing or silently correcting that value. Preserve an honest transition state if reproduced.

## Entity availability, controls, metadata, and diagnostics

Availability correctly incorporates coordinator success and suppresses selected values while charging. Missing fields are filtered when entities are first created, and the multi-sock accumulation fix is retained. However, later availability/value getters directly index fields such as `charging` and the measurement key; missing properties after initial setup can raise exceptions. Optional capabilities appearing only later are not dynamically added. Alert binary sensors remain available while charging, which is a policy to examine with synthetic stale/reset flags rather than assume they indicate live alarms.

The base-station switch is added for every coordinator without a property-capability check. Commands await the library but discard its boolean result and do not request an immediate refresh; displayed state depends on later polling. Current code does not automate alarm silencing, but this is a real control with potential monitoring consequences. Keep it separate from the main physiological card and do not adopt unmerged alarm/recovery controls during maintenance. See [switch.py](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/custom_components/owlet/switch.py).

Metadata includes the serial in a display name. The hardware fallback `3r8` is fabricated for any library object without `hw_version` (including the pinned `Sock`); empty/missing MAC values should not become shared device connections. These are confirmed metadata-quality issues, not evidence of an observed registry collision. Preserve serial-based identifiers when correcting metadata.

There is no `diagnostics.py`, measurement-age entity, repair guidance, or privacy-tested diagnostic export. Prefer a small allowlisted diagnostic summary of versions, anonymous device counts/capabilities, and error/freshness categories. Never export config entries, raw properties, names, serial/MAC/IP values, tokens, or physiological readings. See [official diagnostics guidance](https://developers.home-assistant.io/docs/core/integration_diagnostics/).

## Tests and GitHub Actions

The repository has 27 test functions: four binary-sensor, ten config-flow, three coordinator, six setup, and four sensor tests. They contain useful intent for V2, charging, sleep, authentication, and errors, but import `homeassistant.components.owlet` and `tests.common`, target Core-style fixture loading, and lack a custom-component `conftest.py`/plugin setup. There is no development dependency declaration, pytest configuration, Ruff configuration, socket prohibition, or switch test. Tests last changed in November 2023, before the switch, device-name changes, and API refactors. Mock envelopes still include empty-string `tokens` values, while current code checks key membership and expects a mapping. The device-name/entity-count expectations are also stale. See [tests](https://github.com/Wiggi26/owlet/tree/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/tests).

The sole workflow, [cron.yml](https://github.com/Wiggi26/owlet/blob/f8e0067a1e74a523b0bb4b0841b25404a6926ca8/.github/workflows/cron.yml), runs hassfest and HACS validation on pushes, PRs, and a daily schedule. It uses `actions/checkout@v3`, floating hassfest `master` and HACS `main`, and has no explicit permissions, timeout, dependency matrix, pytest, Ruff, package test, or release job. The HACS action uses its own repository retrieval; its lack of a checkout step is not by itself a confirmed defect.

The newest returned upstream run was [30186310055](https://github.com/ryanbdclark/owlet/actions/runs/30186310055), dated 26 July 2026, at the audited SHA. Both validation jobs succeeded. This establishes historical metadata validation only, not runtime compatibility or a check run today. No fork run was returned. Whether Actions is enabled in the fork remains unverified.

Local audit environment: Python 3.13.15; neither pytest nor Ruff is installed in the selected interpreter. Core 2026.10.2 declares Python `>=3.14.2` in its [project metadata](https://github.com/home-assistant/core/blob/2026.10.2/pyproject.toml). Full pytest/Ruff/hassfest/HACS execution was not performed locally, and no new workflow was dispatched. All tracked Python files passed AST parsing and all JSON files parsed. Isolated synthetic checks confirmed the auth-key error, stale timestamp acceptance, instantaneous oxygen sentinel acceptance, and unknown-as-awake result. These checks used extracted methods and stubs, not an installed Home Assistant runtime or a clinical/device test.

## HACS, manifests, and release packaging

The layout is a single integration under `custom_components/owlet`, with the required manifest domain/name/version/config-flow/requirements fields and a root `hacs.json`. `iot_class` is correctly `cloud_polling`. `hacs.json` selects `zip_release: true` and `filename: owlet.zip`; the inspected upstream archive has integration files at its root and includes all three translations. It contains neither tests nor household data. The fork has no published release/asset yet; end-to-end installation of the fork through HACS has not been verified.

The manifest's documentation and issue tracker, README badges, maintainer text, and release links still point to archived upstream. README installation describes finding Owlet in HACS rather than adding this fork as a custom **Integration** repository. `info.md` uses older HA navigation. Current HACS guidance also calls for integration brand assets, absent here. Update these deliberately after the runtime baseline, while retaining licence/attribution. See [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/) and [HACS manifest/release behaviour](https://www.hacs.xyz/docs/publish/start/).

No packaging/release workflow explains how ZIPs are built. A later workflow should build from an exact tested commit, check an allowlist of runtime files, verify ZIP/tag/manifest version and dependency equality, and produce a reviewable artifact. A downloadable Actions artifact is not a published GitHub release. Do not silently mutate the old upstream tag or overwrite an old version; publish a new fork version only after explicit release approval. There is no deployment runner or HA-host connection to add.

## Privacy and security

Confirmed good practice: current saved entries omit passwords, cloud calls are HTTPS, and the integration itself has no credential files or embedded end-user login. Authentication material still exists in Home Assistant config storage and backups by design; avoid exporting that storage. Setup/coordinator exceptions interpolate the username, and broad flow exception logging can expose details from dependencies. Remove identities from new error text and test redaction.

The inherited fixtures contain raw cloud-property structures, network/device identifier fields, timestamps, and physiological-looking values. Several credential fields are obvious placeholders; some identifier values require provenance review. No synthetic-data provenance is documented. **This is a confirmed exposure surface, not proof of a live credential leak or proof the readings belong to a real baby.** Replace fixtures with entirely generated records before expanding their use. Do not reproduce suspicious values in the audit or public issue discussions.

The dependency contains vendor application constants; those are not proof that this user's account credentials leaked. Do not copy them into documentation. The audit was a source/history review, not an exhaustive secret-scanner certification of every historical blob. If an actual historical exposure is found, remediation must address credential rotation separately from any approved history rewrite.

The integration marks several physiological sensors as measurements, so normal HA recorder/statistics, backups, screenshots, and shared dashboards can retain sensitive information. Document data minimisation and retention choices without altering the user's recorder settings. There is no need for Owlet or Home Assistant secrets in CI. Public examples and diagnostic artifacts must be synthetic and must omit household-specific dashboard configuration.

## UI cards and fit with Baby Monitor

There are no Lovelace/card assets or dashboard examples in this repository. Neither inspected Baby Monitor snapshot contains an Owlet/sock/heart-rate/oxygen binding. The audit therefore evaluates the available dashboard's design structure and a proposed integration seam; it does not claim to have inspected a working Owlet card.

The later snapshot uses three Sections views with a maximum of three columns, reusable `custom:button-card` templates, conditional status banners, camera cards, tiles, care/activity controls, an environment section, and diagnostics. It reuses rounded card styles and compact typography, and several templates explicitly handle unknown/unavailable states. This provides a coherent visual base. The dashboard already depends on button-card, advanced-camera-card, a nursery activity card, and `card_mod`; adding another mandatory card framework would increase maintenance burden.

| Area | Static assessment and proposed acceptance condition |
| --- | --- |
| Placement | Put an optional compact Owlet status group in the existing Baby section; reuse status/summary templates and spacing. Preserve camera and care-action prominence. |
| Hierarchy | Show HR and oxygen with explicit units; label instantaneous and 10-minute average values differently. Put battery, charging, and connection/freshness below them. Omit unsupported measurements gracefully. |
| Honest status | Show separate text states for current, stale, unknown, unavailable, charging, disconnected, and authentication needed. Never render missing values as `0` or a green/healthy indicator. |
| Freshness | Add source age when trustworthy data exists. Neither snapshot currently provides Owlet freshness logic. A front-end clock must not manufacture device freshness. |
| Accessibility | Reuse theme variables, pair colour with text/icons, provide readable units and large touch targets, and avoid continuous animation. Compact 12–13px text seen in styles needs tablet/phone review. |
| Controls | Keep base-station control away from primary readings; require an intentional action/confirmation in any future example. Do not add automatic acknowledgement, recovery-mode toggles, or medical alarm thresholds. |
| Failure and history | Keep stale values out of a live-reading presentation. If history is offered, label it as historical and choose an explicit privacy/retention policy. |
| Rendering | Verify light/dark themes, narrow mobile and target tablet layouts, keyboard/touch use, long translations, slow cloud, and every missing/stale state with synthetic data. No such rendering checks were performed here. |

Dashboard implementation belongs in the Baby Monitor project or a later optional example PR. It must consume existing HA entities without a second Owlet client and must not require entity renames or changes to household dashboards during this audit.

## Upstream history and issue disposition

Key history: May 2023 added reauth, password-free saved entries, refresh fixes, and the original tests; September/November 2023 addressed firmware property differences and V2; March/May 2024 corrected the interval minimum and oxygen-average/charging availability; October 2024 added the base-station switch and state classes; April 2025 refactored API response handling, fixed multi-sock entity accumulation, and rolled the dependency back on `main` after the `2025.4.3` tag. Historical fixes are retained unless a specific regression is demonstrated.

The following inventory accounts for every upstream issue/PR. “Historical” describes disposition and supporting history, not a new end-to-end verification.

| # | Type / state | Maintenance interpretation |
| --- | --- | --- |
| [1](https://github.com/ryanbdclark/owlet/issues/1) | Issue, closed | Early setup report; closed without reproduction; do not treat as confirmed current auth defect. |
| [2](https://github.com/ryanbdclark/owlet/issues/2) | Issue, open | Charging battery spike; report remains unverified. |
| [3](https://github.com/ryanbdclark/owlet/pull/3) | PR, merged | Movement/bucket sensors; already present and disabled by default. |
| [4](https://github.com/ryanbdclark/owlet/issues/4) | Issue, closed | Firmware/revision fields missing; historical changes, retain capability tests. |
| [5](https://github.com/ryanbdclark/owlet/issues/5) | Issue, closed | Alternative integration comparison; no rewrite justified. |
| [6](https://github.com/ryanbdclark/owlet/issues/6) | Issue, closed | Derived sleep duration; dashboard/helper concern, not immediate cloud maintenance. |
| [7](https://github.com/ryanbdclark/owlet/issues/7) | Issue, closed | Missing alert-property setup failure; historical fix and user confirmation. |
| [8](https://github.com/ryanbdclark/owlet/issues/8) | Issue, closed | V2 support; keep covered. App-history interference was reported, not causally established. |
| [9](https://github.com/ryanbdclark/owlet/issues/9) | Issue, closed | Old values/base flags after power loss; critical context for freshness policy. |
| [10](https://github.com/ryanbdclark/owlet/issues/10) | Issue, closed | Slow updates; reporter also saw base disconnected in official app; cause not established here. |
| [11](https://github.com/ryanbdclark/owlet/issues/11) | Issue, closed | UI minimum exceeded default; five-second correction already present. |
| [12](https://github.com/ryanbdclark/owlet/pull/12) | PR, closed unmerged | One-second polling rejected; preserve conservative cadence. |
| [13](https://github.com/ryanbdclark/owlet/issues/13) | Issue, closed | Historical `DeviceInfo` import issue attributed to old Core, user confirmed upgrade resolved it. |
| [14](https://github.com/ryanbdclark/owlet/pull/14) | PR, merged | 255 oxygen-average guard already included; instantaneous values still need validation. |
| [15](https://github.com/ryanbdclark/owlet/issues/15) | Issue, closed | V2 discovery metadata and old-Core failures; retain regression coverage. |
| [16](https://github.com/ryanbdclark/owlet/issues/16) | Issue, open | Camera support request/research; separate future scope. |
| [17](https://github.com/ryanbdclark/owlet/issues/17) | Issue, open | Predicted sleep-window feature; API availability unverified, defer. |
| [18](https://github.com/ryanbdclark/owlet/pull/18) | PR, merged | French translation present; visible encoding artifacts need later review. |
| [19](https://github.com/ryanbdclark/owlet/issues/19) | Issue, closed | Base-station switch request; implemented historically. |
| [20](https://github.com/ryanbdclark/owlet/issues/20) | Issue, closed | Missing measurement state classes; historical correction present. |
| [21](https://github.com/ryanbdclark/owlet/issues/21) | Issue, closed | Movement can be enabled through the entity registry; do not instruct source edits. |
| [22](https://github.com/ryanbdclark/owlet/issues/22) | Issue, closed | Duplicate base-control request; already implemented. |
| [23](https://github.com/ryanbdclark/owlet/pull/23) | PR, merged | README install edit; retained, but fork-specific guidance still needed. |
| [24](https://github.com/ryanbdclark/owlet/issues/24) | Issue, closed | Multi-sock regression and stale test-setup discussion; motivates multi-device tests. |
| [25](https://github.com/ryanbdclark/owlet/pull/25) | PR, merged | Entity accumulation fix present; naming/metadata changes explain stale tests. |
| [26](https://github.com/ryanbdclark/owlet/issues/26) | Issue, open | Recovery-mode control request; defer safety-sensitive feature work. |
| [27](https://github.com/ryanbdclark/owlet/issues/27) | Issue, open | Options-flow deprecation confirmed separately; its no-devices report has no reproduced cause. |
| [28](https://github.com/ryanbdclark/owlet/pull/28) | PR, open | Alarm acknowledgement plus a Git-pinned library fork; do not adopt during maintenance. |
| [29](https://github.com/ryanbdclark/owlet/issues/29) | Issue, open | Incompatible release pin: tag confirmed, current uploaded ZIP differs as described above. |
| [30](https://github.com/ryanbdclark/owlet/pull/30) | PR, open | Region-aware account migration; review separately with identity/privacy tests. |
| [31](https://github.com/ryanbdclark/owlet/issues/31) | Issue, open | Frozen readings report; freshness gap confirmed, actual cause unverified. |

## Review outcome

Preserve the architecture and existing identities. Establish executable offline tests first, repair Core options/reauth paths second, then address measurement validity and freshness. Packaging, diagnostic exports, dependency upgrades, and dashboard examples follow in focused changes. See [ROADMAP.md](ROADMAP.md) for scope, acceptance criteria, and release gates. No implementation, push, PR creation, release, or deployment is part of this audit delivery.
