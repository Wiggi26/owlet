# Testing

## Environment and local checks

Tests run on Linux. Use Linux directly or WSL on Windows; no Home Assistant server or Owlet credentials are needed. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) **0.13.1**. Direct dependencies are pinned in `pyproject.toml`; `uv.lock` records transitive versions and artifact hashes. The test plugin provides Home Assistant fixtures, pytest, pytest-asyncio, controlled time, coverage and socket blocking.

| Profile | Home Assistant | Python | Custom-component test plugin |
| --- | --- | --- | --- |
| Baseline | 2025.12.4 | 3.13.2 | 0.13.301 |
| Current stable | 2026.10.2 | 3.14.2 | 0.13.373 |

These are compatibility probes, not a claim that all features work on either release. Known defects are listed below. Changing either profile requires reviewing the plugin's exact Core/pytest requirements and updating the workflow, dependency markers, lockfile and version-specific naming assertions together.

Baseline evidence: both GitHub matrix jobs at `121aa2d` report **56 passed, 7 strict expected failures, 97.53% combined line/branch coverage** in [run 39158262400](https://github.com/Wiggi26/owlet/actions/runs/39158262400). Final-head checks are linked in the PR. Local Linux verification uses the same profiles and thresholds; `--tb=line --show-capture=no` can shorten traceback rendering on slow WSL mounts without changing test execution.

Run the current profile and quality checks from the repository root:

```sh
uv sync --locked --python 3.14.2
uv run --no-sync pytest -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync zizmor --offline .github/workflows
uv run --no-sync pip-audit --strict --progress-spinner off
git diff --check
```

Run the baseline in a separate environment:

```sh
UV_PROJECT_ENVIRONMENT=.venv-baseline uv sync --locked --only-group test --python 3.13.2
.venv-baseline/bin/python -m pytest -q
```

On WSL, keep environments on the Linux filesystem for better performance. The default `.venv` and alternate `.venv-*` directories are ignored. `uv lock` deliberately updates dependencies; ordinary local and CI runs use `--locked`. The integration's runtime requirement remains `pyowletapi==2025.4.1` in `manifest.json`; development dependencies are not installed by HACS.

## Workflow

`.github/workflows/validate.yml` runs on PRs targeting `main` and pushes to `main`, using GitHub-hosted Ubuntu 24.04 runners and read-only repository contents permission. A newer run cancels the previous run for the same PR/ref. Feature-branch pushes do not duplicate PR jobs. No scheduled, deployment, publishing or privileged PR-target job is configured.

- **Quality:** Ruff lint and formatting across source/tests, plus offline zizmor workflow-security analysis.
- **Tests:** both exact Core/Python profiles, real custom-component loading, branch coverage and a 90% combined line/branch threshold. Matrix failures are independent; neither is allowed to fail silently.
- **Dependencies:** pip-audit checks the installed, locked current-Core test/tool environment and fails on known advisories or audit errors. The historical baseline environment is not covered by this advisory job. An advisory result is a dated database check, not a security guarantee.
- **Metadata:** Home Assistant hassfest and HACS integration validation. These complement runtime tests.

HACS and hassfest run in their official CI container actions. They were not run in the local WSL environment, where no Docker daemon is available; use the linked PR jobs for their results.

Actions are pinned to reviewed commits; uv and Python are pinned separately. Upstream HACS/hassfest action wrappers still use their maintained container images. Dependabot proposes action and uv updates for review; it cannot merge them. Test output and coverage summaries stay in job logs; no account data, backups or live captures are required.

## Mocking and fixtures

`tests/conftest.py` enables custom integrations and supplies `MockConfigEntry` from `pytest_homeassistant_custom_component.common`. Tests import `custom_components.owlet`; they do not depend on Core's private `tests.common` or a Core Owlet implementation.

`tests/fixtures/*.json` retains the six original filenames with independently authored synthetic discovery, token-rotation, V2 and V3 asleep/awake/charging responses. Addresses, identifiers, tokens, timestamps and readings are invented. `tests/fixture_data.py` loads these baselines during collection, returns fresh copies and applies field overrides for edge cases. See the [fixture provenance](../tests/fixtures/README.md). The real pinned `Sock` parser normalises these responses. Authentication, discovery, property reads and command writes are mocked at `pyowletapi` boundaries. Unexpected request, activation, credential-exchange, refresh or close calls raise and also fail fixture teardown, even when application exception handling swallows the error.

pytest-socket blocks network sockets, allowing Unix sockets for the event loop. Never add real credentials, enable network access, or relax the guards to make a test pass. Use the freezer fixture and explicit coordinator refreshes instead of sleeping. Switch tests exercise only mocked commands.

## Baseline and confirmed defects

Coverage includes configuration/duplicate-account flows, reauthentication, setup/unload/reload, token rotation, discovery errors, connection failures/timeouts, malformed responses, V2/V3 entity creation, two-sock isolation, state/availability changes, charging, switches and registry/config identity preservation. Naming assertions distinguish newly generated entity IDs on the two Core versions; reload checks preserve already registered IDs and user customisations.

At current reconciled main `d178a33`, only the stale-source regression below remains as a strict expected failure for a known defect from [AUDIT.md](AUDIT.md). Its marker matches a checked exception or dedicated failure class; unrelated failures remain failures. No whole module is skipped.

| Regression | Finding / follow-up |
| --- | --- |
| `test_old_source_measurement_unavailable` | Years-old source readings remain available; OWL-011 / [#11](https://github.com/Wiggi26/owlet/issues/11) |

Merged options/default, saved-interval, sleep/numeric-validity, polling-reauth and normalized-getter fixes removed their matching markers. PR #39 also fixed integration-owned error/log privacy paths; it did not remove an expected-failure marker. Exact tested versions/results and remaining manual gates are in the [audit reconciliation](AUDIT.md#merged-evidence-reconciliation--19-october-2026).

The merged [raw-parser contracts](RAW_PROPERTIES.md) characterize remaining defects; passing them does not establish field isolation. The [battery investigation](BATTERY.md) verifies synthetic input exposure without identifying a production cloud/firmware cause.

The stale-data regression uses an obviously historical timestamp to expose the missing guard. It does not prescribe a universal freshness cutoff. Passing tests and expected failures are reported separately; neither metadata validation nor coverage certifies live cloud/device compatibility.

Flow tests also record the current generic `unknown` response to connection/timeouts and missing reauth feedback. Actionable error classification and translations remain open roadmap work.

## Adding regressions and remaining gaps

Add or update synthetic JSON baselines for complete response scenarios; use helper overrides for individual edge cases. Test the intended behaviour through the actual integration/HA APIs. Assert entry IDs, data/options, entity unique IDs and registry bindings when touching setup or reload. Verify failure followed by recovery. New regressions normally fail until fixed; use a narrow strict expected failure only for a confirmed baseline defect, with its exact signature, audit reference and named follow-up. Never weaken assertions or exclude modules to obtain green CI.

Further coverage is needed for concurrent account refresh, partial token exchanges and process-restart/storage persistence, HTTP/backoff handling beyond the [retained-library contracts](LIBRARY_CONTRACTS.md), device rediscovery, raw malformed-field isolation, timestamp/firmware validity cases, diagnostics redaction, and an actual cross-Core registry-storage migration. No live Dream/European-account or hardware acceptance test is included. The original CI baseline changed source only mechanically; subsequent runtime fixes are recorded separately in the audit.
