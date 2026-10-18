# Owlet maintenance engineering rules

## Scope and review gate

This public fork maintains the existing Home Assistant custom integration for Owlet. The target installation is a Smart Sock 3 used with the Owlet Dream app, including European accounts, on Home Assistant OS running on Proxmox.

The integration is supplemental to the official Owlet app, base station, and alarm system. Do not describe Home Assistant readings, notifications, or dashboard colours as medical advice, a safety guarantee, or a replacement alarm system. Never add automatic alarm acknowledgement, silencing, or changes to official monitoring behaviour as a maintenance shortcut.

The current authorised work is public-fork HACS packaging, repository metadata, installation documentation, and related validation. This supersedes the original documentation-only audit phase; runtime roadmap work still needs separate authorisation. Do not change application functionality, dependency pins, configuration entries, entity identifiers, or dashboards in this packaging change. Do not deploy, merge, or publish a release. Stop after preparing or updating one focused pull request.

## Documentation and review preferences

- Keep PR descriptions concise: describe the change, relevant checks, and unresolved issues. Keep detailed verification evidence in the audit or packaging document instead of repeating it.
- Limit README edits to factual behaviour, usage, installation, upgrades, and troubleshooting relevant to the change. Keep audit narratives, implementation plans, and release-process details in `docs/`.
- Preserve existing integration names; do not add fork or owner branding to titles or display names. Use owner handles where needed for repository URLs and code ownership; avoid repeated maintainer references.
- Preserve upstream attribution and the licence. Add or change attribution/licensing material only as needed to retain notices, identify modifications, or distribute the licence with installed files. Avoid duplicate attribution and modification banners.

## Compatibility comes first

- Keep the integration domain and package path `owlet` and `custom_components/owlet`.
- Preserve existing entity IDs, entity unique IDs, device identifiers, registry associations, disabled states, and user customisations. The existing entity unique ID convention is `<sock serial>-<property key>` within each platform. Do not rename existing devices, translation keys, or entities casually: these can affect generated names for new installations.
- Preserve configuration entry IDs, account identity, version, data, and options. Existing keys include `region`, `username`, `api_token`, `expiry`, `refresh`, and the `scan_interval` option. Do not require removal and reinstallation as a migration strategy.
- Any necessary configuration or registry migration needs a focused explanation, upgrade tests with old entries, and evidence that dashboard and automation bindings survive. A region-aware account identity must not change entity unique IDs.
- Keep V2 and other previously supported devices working unless a separately reviewed support change explicitly says otherwise. Test multiple socks on one account.
- Keep the coordinator and cloud-library architecture. Prefer small fixes over a rewrite or vendoring a second cloud client.
- Declare only Home Assistant and Python versions that CI actually verifies. Match Python to each tested Core version. The inherited HACS minimum is not proof of runtime compatibility.

## Cloud, authentication, and asynchronous work

- Keep external communication in `pyowletapi`; maintain an exact, reviewed dependency pin in the integration manifest. Review the package's imports, exception hierarchy, return shapes, refresh behaviour, and Python requirements before changing that pin. A newer version is not automatically compatible.
- Use Home Assistant's shared asynchronous HTTP session. Do not close a session owned by Home Assistant. Avoid blocking HTTP, filesystem work, subprocesses, or sleeps on the event loop.
- Distinguish invalid credentials from temporary network errors, timeouts, server failures, and throttling. Authentication failures must reach Home Assistant's reauthentication mechanism; transient failures must be retryable without deleting configuration.
- Persist refreshed tokens together without losing existing entry data or options. Never persist the user's password. Cover restart after refresh, failed refresh, and concurrent access by multiple sock coordinators.
- Preserve the selected cloud region. Do not silently switch an existing European account to `world`, probe other regions with credentials, or assume a device's purchase location determines its account region.
- Keep cloud polling at five seconds or slower unless a separately reviewed change has credible API evidence. Account for all requests made by the library, not just coordinator invocations. Bound requests, respect throttling, and avoid overlapping refresh storms.
- Apply changed options to the running integration through a supported reload or update mechanism. Clean up listeners and runtime state on unload.

## Measurement integrity and entity behaviour

- Treat successful HTTP transport, a successful poll, and a fresh device measurement as different facts.
- Use trustworthy source timestamps and validity indicators where available. Never infer freshness solely from a changing Home Assistant timestamp or from whether a reading's numeric value changes.
- Preserve UTC/timezone information when comparing timestamps. Test old, missing, malformed, and future timestamps, clock skew, and recovery. Do not invent a freshness threshold without documenting its evidence and limitations.
- Expose missing, invalid, stale, charging, disconnected, or unsupported measurements honestly as unknown or unavailable, according to documented semantics. Never fill missing physiological readings with zero, clamp invalid readings into a plausible range, or carry old readings forward as current.
- Distinguish an unknown sleep state from awake or asleep. Do not interpret new firmware codes using a guessed physiological meaning.
- Avoid one malformed or missing optional property breaking all entities. Keep transport availability and measurement validity separate where appropriate.
- Preserve the existing base-station switch identity. Changes to its safety, defaults, command handling, or presentation require their own focused review; never put it in an unattended alarm-silencing automation.

## Tests and validation

Use pytest, Ruff, Home Assistant hassfest, and HACS validation. The inherited repository lacks a runnable custom-component test harness and development dependency declaration; roadmap PR 1 establishes these. Until then, report that limitation instead of claiming tests pass.

After that harness exists, the standard local checks are:

```text
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
git diff --check
```

- Run integration tests on Linux in GitHub Actions with explicit Home Assistant/Python pairs. Include the declared minimum and a pinned current stable Core version; update the latter deliberately. Report the exact versions tested.
- Enable custom integrations through the pytest Home Assistant custom-component harness and patch the actual `custom_components.owlet`/library boundaries. Do not import a nonexistent Core `homeassistant.components.owlet` implementation or depend on Core's private `tests.common` package.
- Mock every cloud interaction, including authentication, device discovery, polling, refresh, activation writes, and switch commands. Disable real network sockets in the test suite. Use controlled time rather than real delays.
- Use entirely synthetic fixtures and identities such as `example.invalid`. Cover setup, reload/unload, options, reauthentication, entry preservation, multiple devices, token rotation, transient errors, invalid data, stale data, and recovery as relevant to each change.
- Do not hide failing tests, weaken assertions, or perform broad formatting churn to obtain a green check. For a confirmed pre-existing defect only, a narrowly scoped strict expected-failure test may establish the initial baseline: it must execute, match the specific known failure, cite the finding, and identify the fix PR that removes it. Never exclude a whole module or imply an expected failure proves compatibility.
- Run hassfest and HACS validation on pushes and pull requests only; do not add scheduled runs unless explicitly requested. Validate the packaged integration as well as the source tree before any later release. Metadata validation does not replace runtime tests.
- Documentation-only changes need link/path, scope, sensitive-data, and whitespace checks; do not invent application test results for them.

## Privacy and security

- Never commit credentials, access or refresh tokens, personal information, baby health data, household dashboards, device/network identifiers, or live cloud responses. Do not publish them in issues, PR descriptions, CI logs, screenshots, diagnostics, or artifacts either.
- Use synthetic data rather than merely removing an account name from a real capture. Review inherited fixtures for provenance before expanding or republishing them.
- Keep Home Assistant `.storage`, `secrets.yaml`, login files, HAR captures, logs, backups, and exports outside Git. Ignore rules are convenience controls, not evidence that a file is safe.
- Redact error messages and logs. Prefer a diagnostics allowlist containing versions, supported capabilities, anonymous device counts, and freshness/error categories; omit credentials, identities, network details, readings, and raw payloads. Test nested redaction and unexpected fields.
- Keep development and CI independent of Owlet credentials and Home Assistant access. Use least-privilege workflow permissions and reviewed action revisions; untrusted PR code must not receive secrets.
- If an actual exposure is discovered, stop reproducing its contents and record only redacted evidence. History rewriting or credential rotation is a separate, explicit action, not an automatic audit step.

## Dashboard boundary

Keep dashboard examples optional and separate from the Python integration. Fit the Baby Monitor project's existing Sections layout and reusable status/action templates. Show units, source/freshness status, and charging/disconnection/unknown states in text as well as colour. Keep physiological values visually separate from control actions. Do not add a required custom card dependency or a second cloud polling loop merely to display entities.

Public examples must use placeholder entity IDs and synthetic readings. Never copy the household dashboard snapshots into this repository. A source review is not proof of tablet, mobile, accessibility, light-theme, or dark-theme rendering; record which checks were actually performed.

## Git, PRs, and delivery

- Use a separate Git worktree and a short, single-purpose branch for each change. Inspect status and existing worktrees first. Keep the main checkout and unrelated user changes intact.
- Keep PRs small and reviewable. Explain the concrete problem, resulting behaviour, compatibility impact, test evidence, and remaining uncertainty. Attribute upstream fixes and preserve the Apache-2.0 licence.
- Mark findings as confirmed from source/offline checks, upstream reports, or unverified hypotheses. An issue's closure or a successful metadata workflow does not prove a runtime defect is fixed.
- GitHub Actions provides testing and validation. Installation and updates go through the public fork as a HACS custom integration. There is no deployment runner, SSH deployment, or direct Home Assistant access in this workflow.
- Do not create deployment credentials, connect to the user's Home Assistant, manipulate Proxmox, publish releases, merge PRs, or change official Owlet monitoring as part of routine maintenance. Release publication remains a separate user decision.

See [the audit](docs/AUDIT.md) for evidence and [the roadmap](docs/ROADMAP.md) for the proposed first three implementation PRs.
