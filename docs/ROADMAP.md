# Owlet maintenance roadmap

Prepared 18 October 2026 from [AUDIT.md](AUDIT.md). Runtime work remains a proposed plan for review. Public-fork packaging and documentation were separately authorised ahead of this sequence; see [PACKAGING.md](PACKAGING.md). No deployment, release publication, merge, or household dashboard change is authorised.

## Priorities and constraints

Maintain `owlet` and its existing entity/configuration identities. Keep the unofficial cloud library and coordinator architecture. The target is Smart Sock 3 with the Dream app and European accounts; retain V2 and multiple-device compatibility. Home Assistant remains supplemental to the official Owlet alarm system.

P1 work establishes a reproducible test baseline, fixes current Core/options and authentication handling, and prevents invalid/stale readings from being presented as current. P2 work improves recovery, diagnostics, distribution, documentation, and dashboard fit. Camera support, derived predictions, recovery-mode control, alarm acknowledgement, and a wholesale rewrite are deferred.

At the original audit, the fork matched upstream `main` at `f8e0067`. Keep `pyowletapi==2025.4.1` through the first three runtime PRs unless a separately reviewed requirement makes that impossible. Do not use the upstream `2025.4.3` tag as an interchangeable baseline: its pin differs from `main` and the uploaded ZIP.

## Proposed first three implementation PRs

These are the first three PRs **after approval of the documentation**, not three PRs to create now. Use separate worktrees and branches; merge in order. Each must pass its declared checks. The infrastructure baseline must report specific known regressions openly; PRs 2 and 3 replace their expected-failure cases with passing behaviour tests. If a PR needs unrelated runtime changes to become green, split or revise its scope rather than weakening checks.

### PR 1 — Establish an offline custom-integration test and CI baseline

Suggested branch: `test/offline-ci-baseline`. Priority: P1. Runtime application changes: none.

Problem: the existing 27 tests target Home Assistant Core's source tree, lack a declared test environment, and are not run by Actions. Their mocks and expected device/entity names predate runtime changes. Fixtures contain capture-like data without synthetic provenance.

Scope:

- Add pinned development dependencies and pytest configuration using `pytest-homeassistant-custom-component`, with custom integrations enabled and real sockets disabled. Match its Home Assistant version constraints rather than blindly combining incompatible pins.
- Convert test imports, patch targets, and fixture loading to this repository's `custom_components.owlet` implementation. Generate entirely synthetic fixtures; update stale response envelopes and expectations to the audited baseline. Do not change existing unique IDs to satisfy tests.
- Preserve useful existing setup, flow, sensor, binary-sensor, and error tests. Add a minimal switch/multi-sock baseline and identity assertions. Where an existing assertion exposes a confirmed runtime defect, retain its intended behaviour as a narrow strict expected-failure regression with the specific failure signature and audit reference; remove that marker in PR 2 or 3. Do not skip whole tests/modules or relax assertions to claim the defect is fixed. Record the exact Core/Python/library versions.
- Add Ruff configuration, `ruff check`, and `ruff format --check`; keep unrelated formatting out of this PR. If existing application formatting prevents a full-tree gate, propose a separate mechanical-only follow-up or an explicit temporary baseline with a removal issue. Do not silently exclude runtime files.
- Add pytest and Ruff Actions jobs; retain hassfest and HACS validation. Pin reviewed action revisions, set `permissions: contents: read`, job timeouts, and concurrency cancellation. Use `pull_request`, not a privileged untrusted-code execution path. No Owlet/HA secrets or deployment jobs.
- Declare how to reproduce checks locally and on Linux Actions. Test an explicit currently workable Core/Python pair first; identify the minimum/current compatibility failures as separate regressions for PR 2. Full application support on current Core is not a claim of this infrastructure PR.

Acceptance:

- A clean Linux CI run collects and runs the ported tests against this custom integration, with network sockets prohibited. A forgotten mock fails instead of contacting Owlet, including activation POSTs and command calls.
- Every fixture is synthetic, with no household names, real readings, device/network IDs, credentials, or captured timestamps. No debug payload appears in CI logs/artifacts.
- Ruff, hassfest, and HACS outcomes are explicit and reviewable. Pytest reports executed/passed/strict-expected-failure totals separately; only the documented defects assigned to PR 2 or 3 qualify for expected failure. Unexpected failures block the PR, and unexpected passes require removing the marker. Lint/metadata failures are resolved within scope or the PR is split.
- Existing entry data/options, serial-based entity unique IDs, and multi-device creation are covered. No application behaviour, dependency pin, manifest version, release, or deployment changes occur.

### PR 2 — Repair current Core options and reauthentication handling

Suggested branch: `fix/options-and-reauth`. Priority: P1. Depends on PR 1.

Problem: current Core rejects the options constructor's `config_entry` assignment. Polling authentication errors raise `KeyError('email')` instead of reaching reauth. Connection/no-device/reauth failures lack consistent user feedback, and changed intervals do not reach running coordinators.

Scope:

- Use the supported options-flow property without manually assigning it. Apply changed polling intervals through one supported reload/update mechanism; provide a default for older entries missing the option and keep the five-second minimum.
- Correct the polling auth exception path using non-identifying error text. Preserve entry ID, `username`, `region`, tokens, all existing data/options, and entity registry identities during reauth/reload.
- Use supported reauth helpers, classify connection/credential/no-device failures, and supply every emitted translation key. Validate supported-device discovery before completing initial setup, while keeping transient service failures retryable.
- Retain exact token dictionary persistence and add tests for refresh followed by restart and a failed/partial exchange. Do not persist passwords. Identify any account-wide refresh-lock/library change as a separate follow-up if the contract cannot be fixed in this focused PR.
- Replace the unverified `2024.1` compatibility claim with an explicit tested support policy. Proposed modern baseline for review: Core 2025.12 plus Core 2026.10.2/current stable at implementation time, using the matching Python versions. Check whether a less disruptive floor is practical; do not advertise a range CI does not exercise.

Acceptance:

- Options open and save on the chosen current Core; changed polling takes effect without deleting/re-adding the integration. Existing saved intervals are retained and absent values receive the documented default.
- Synthetic expired/revoked tokens trigger reauth; network/server failures produce retryable failures; incorrect credentials and an empty/unsupported account produce translated guidance.
- Reauth and reload preserve entry IDs, entity IDs/unique IDs, devices, options, and region. Restart after a mocked refresh uses the new token set without a password.
- The declared minimum and current stable Core/Python CI jobs pass, including import/setup/options tests. `pyowletapi` remains pinned to 2025.4.1; no region-identity migration, release, deployment, or dashboard change is included.

### PR 3 — Validate physiological values and expose honest freshness states

Suggested branch: `fix/measurement-validity`. Priority: P1. Depends on PRs 1 and 2.

Problem: successful polls accept old source data, instantaneous oxygen lacks sentinel validation, unknown sleep codes become awake, and disappearing properties can break entity getters. Upstream frozen-reading reports establish a reason to investigate; they do not establish the current device's root cause.

Scope:

- Create a small validated measurement snapshot at the existing library/coordinator boundary, retaining raw UTC source time where available. Keep transport success distinct from device measurement validity and preserve all entity unique IDs.
- Define and document a source-age policy supported by the API fields and synthetic replay scenarios. Handle absent/malformed/future timestamps explicitly. If reliable freshness cannot be determined for a device/firmware, expose that uncertainty rather than inventing a fresh timestamp or inferring staleness merely from identical values.
- Reject oxygen sentinels/out-of-range values and non-finite/malformed numeric measurements. Define non-medical validity rules for other fields using protocol evidence, not alarm thresholds. Preserve the existing 10-minute average guard and charging semantics.
- Make unknown/new sleep codes unknown; protect getters against missing properties. Distinguish stale/invalid values from transient cloud failure and document recovery semantics for alerts as well as measurements.
- Add only the additive freshness/status metadata needed for a later dashboard. Do not bundle a diagnostic export, a card implementation, new cloud polling, or an alarm feature into this PR.

Acceptance:

- Frozen source timestamps, repeated valid identical readings, invalid/missing/future timestamps, old replayed values, charging, missing fields, disconnects, source recovery, oxygen sentinels, NaN/infinity, and new sleep codes are covered with synthetic controlled-time tests.
- Unknown sleep never becomes awake by default. Invalid/stale physiological values do not appear as valid zeroes, plausible clamped values, or current “healthy” readings. Valid live and historical measurements remain distinguishable.
- Tests verify no entity/config identity changes, multi-sock independence, and bounded polling. No live account is used and no clinical threshold or reliability guarantee is introduced.
- The PR states limitations, especially when cloud timestamps might advance without new device measurements. If a trustworthy source-age rule cannot be established, land the validated parts with explicit unknown freshness and track the unresolved protocol question separately.

## Subsequent focused work

| Order / priority | Work | Completion evidence |
| --- | --- | --- |
| 4 / P1 before release | Reproducible fork packaging and HACS instructions | Source-directory HACS packaging and fork docs addressed separately; see PACKAGING.md. Validate the selected ref's extracted integration, translations, licence/attribution, tag/manifest/dependency equality, and absence of private files. No uploaded release ZIP or ZIP-build workflow is required. Tested runtime support and user-run HACS acceptance remain release gates. No publication in this work. |
| 5 / P2 | Cloud resilience and token concurrency | Mock timeouts, cancellation, 401/403/429/5xx, `Retry-After`, disconnect/reconnect, concurrent socks, and token rotation. Add account-wide refresh coordination/backoff at the correct layer without lowering the poll interval. Measure request amplification and test unload cleanup. |
| 6 / P2 | Dependency-contract review | Compare 2025.4.1 with 2025.4.10 or a maintained successor; test removed exception classes, device filtering, normalisation, refresh, commands, and Python/aiohttp compatibility. Choose a tested exact pin; do not use a Git fork just to obtain an alarm button. |
| 7 / P2 | Privacy-safe diagnostics and metadata | Allowlisted diagnostic summary with nested redaction tests and synthetic output. Correct invented hardware versions/invalid MAC connections while preserving registry identifiers. Explain recorder/statistics/backup sensitivity. |
| 8 / P2 | Optional Baby Monitor card example | Reuse Sections and existing status/summary templates; keep camera/care hierarchy; HR/oxygen/average units, charging/battery, trustworthy source age, unknown/stale text, and optional capabilities. Synthetic-only examples; mobile/tablet and theme/accessibility review; no household dashboard export or new required framework. |
| 9 / P2 | Account-region identity and translations | Review upstream PR #30 as a separate migration, with duplicate-account/region tests, preserved entity identities, and no account identifiers in logs. Review French encoding and the English content of the Ukrainian locale; keep existing translation keys stable. |

If a confirmed credential exposure emerges, address it immediately with redacted evidence and a separate authorised remediation path. The audit has not established an active credential leak, and this contingency is not a reason to rewrite public history now.

## Validation and release gates

For approved implementation work, run pytest with all network blocked, Ruff lint/format checks, hassfest, HACS validation, and `git diff --check`. Runtime matrix entries must specify compatible Python/Core/test-plugin constraints. Test the selected source ref's HACS-extracted contents and import/setup path; passing metadata validation alone is insufficient.

Before any release decision, provide the exact candidate commit/version, green check links, package inspection result, tested Core/Python versions, identity/migration evidence, known cloud/firmware limitations, installation/restart instructions, and a rollback plan. Rollback must account for any config migration; downgrading code is not automatically a safe data migration.

The owner may later verify the approved candidate through HACS on their own HA OS installation and compare synthetic/test behaviour or ordinary operation with the official app. That is a separate user-run acceptance step, not a request for credentials, direct HA access, SSH, or deployment infrastructure. Do not publish those household observations as baby readings.

Build/validation artifacts may be prepared for review during approved work. Publishing a GitHub release, installing to Home Assistant, merging PRs, and changing monitoring/control behaviour are separate actions. The authorised packaging follow-up stops at a pull request; the proposed runtime PRs still await separate authorisation.
