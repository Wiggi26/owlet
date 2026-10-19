# Core log privacy investigation

The [characterization tests](../tests/test_core_log_privacy.py) reproduce
entry-title exposure through real Home Assistant setup, reload and reauthentication
APIs. Passing them does not repair privacy. This is partial evidence for
[#6](https://github.com/Wiggi26/owlet/issues/6) (OWL-007), following the
integration-owned sanitization in [PR #39](https://github.com/Wiggi26/owlet/pull/39).

## Observed behavior

Both locked [profiles](TESTING.md) expose the complete entry title in Core's
setup-failure messages. The default title is the username. Custom titles appear
literally, including identifying text unrelated to the username. A neutral custom
title keeps the username out of these messages; arbitrary custom titles remain
potentially identifying.

| Core / Python | Initial setup logger | Failed setup after reload | Retry message level | Debug exception records |
| --- | --- | --- | --- | --- |
| 2025.12.4 / 3.13.2 | `homeassistant.config_entries` | `homeassistant.config_entries` | DEBUG | None in these paths |
| 2026.10.2 / 3.14.2 | `homeassistant.config_entries` | `custom_components.owlet` | INFO | Sanitized setup and polling exceptions |

Current Core's initial component setup supplies an integration without populating
the entry's cached integration; later setup resolves that cache and can route
Core messages to the integration logger. Logger name alone cannot establish who
generated a message. Tests also identify Core records by source file; they do not
replace logging calls.

Authentication failures at WARNING include the title and `Credentials expired`
or `Authentication failed`. Retry logs include the title and retry notice.
Authentication-stage connection failures retain `Error connecting to Owlet`.
First-refresh connection failures produce an empty `ConfigEntryNotReady` message:
the category survives in current Core's DEBUG `UpdateFailed` cause, but is absent
from baseline's captured logs.

Full formatting includes visible chains and notes. Nested synthetic passwords,
tokens, device/network identifiers, reading markers, unexpected fields, causes
and notes remain absent. The username appears only through the default title.

Polling and failed reauthentication logs omit titles in these paths. Core retains
the title in reauth UI context. Recovery preserves the entry's identity, title,
version, data and options; existing [registry tests](../tests/test_polling_reauth.py)
cover bindings.

## Remedy boundary and next design

The inspected Core paths offer no separate per-entry log label. Sanitizing an
integration exception cannot remove Core's independent title interpolation.
Temporary title mutation misses failures before/after setup and later tasks,
retries and reauth UI.

Supported `async_update_entry(title=...)` retains the entry but changes its
presentation title, violating custom-title preservation. Neutral defaults for new
entries leave existing/custom identifying titles exposed.

Core's `logger` integration supports operator-configured levels and regex filters.
Filters drop matching message records; they do not redact formatted chains.
Suppression must cover both logger names/timings, loses useful categories and can
affect other integrations on the shared logger. This is incomplete mitigation.

Next, review a Core-level safe logging label/redaction facility independent of the
stored title, covering initial setup and retry/reauthentication while retaining
custom titles, identities and useful categories. No suitable integration-only hook
was established in these versions; the design remains unresolved. No runtime,
title, filter or dependency change is made here.

## Verification and remaining limits

Focused Linux execution: **16 passed** per profile, sockets blocked and cloud calls
mocked; no new skips/expected failures. Broader checks belong in the PR record.

Keep #6 open pending a reviewed remedy and synthetic log/example-report acceptance.
Switch-command privacy remains unverified with
[#15](https://github.com/Wiggi26/owlet/issues/15). These contracts establish no
whole-system, diagnostic-export or live-device privacy guarantee.
