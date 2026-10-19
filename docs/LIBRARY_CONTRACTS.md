# Retained cloud-library contract preflight

This is the offline preflight for [OWL-017 / issue #7](https://github.com/Wiggi26/owlet/issues/7),
reviewed on **19 October 2026**. The decision is to retain
`pyowletapi==2025.4.1`. No integration code, dependency pin, configuration,
workflow, entity identity or official monitoring behaviour changes here.
Observed library behaviour is recorded as a baseline for later fixes; passing
these assertions does not make that behaviour desirable or resolve the related
runtime findings in the [audit](AUDIT.md#remediation-register).

## Evidence and package review

The previously downloaded public source distributions recorded in the
[audit](AUDIT.md#dependency-versions-and-release-mismatch) were reviewed offline.
The retained archive is available locally, and the installed distribution is
available in both locked Linux environments. This preflight does not recheck
current package-index availability or select a newer release.

| Distribution | Cached sdist SHA-256 |
| --- | --- |
| 2025.4.1 | `39c32fe5623d8c17eda43e12740ac5296fa60c27475070db69d775b53a1684a5` |
| 2025.4.8 | `66a65d74b851edd7835c887bb0d47625a5396b59d4506df41b45aae63349faf0` |
| 2025.4.10 | `33a21c77adcc04663fcdbf1a0e845f37190512d72f662bc61c4cabeaf3c4b785` |

All six installed Python source files match the retained sdist byte for byte;
the same source hashes were observed in both profiles. Relevant source hashes:

| Retained source | SHA-256 |
| --- | --- |
| `api.py` | `737ce4c79eeeb66d6a352f202a93b9ec6a125d524d7d51ca8e54c52d4697f082` |
| `exceptions.py` | `2531383ac6e580a408a98bc3bb2a023c1f1b0c2abdb9dbb8d8fc8d72b80582d3` |
| `sock.py` | `12e53aef51a44fc965d41844a8bd7da7c917e773805c58ca3ce9691fd59e5ab2` |

Retained installed metadata and the archive's dependency metadata declare Python
`>=3.10` and an unbounded `aiohttp` requirement. These requirements are not a
Home Assistant support policy. The exact locked combinations exercised here are:

| Profile | Home Assistant | Python | Test plugin | aiohttp | pyowletapi |
| --- | --- | --- | --- | --- | --- |
| Baseline | 2025.12.4 | 3.13.2 | 0.13.301 | 3.13.2 | 2025.4.1 |
| Current | 2026.10.2 | 3.14.2 | 0.13.373 | 3.14.5 | 2025.4.1 |

The historical source comparison establishes that 2025.4.8 and 2025.4.10 remove
`OwletEmailError` and `OwletPasswordError`, which this integration imports.
2025.4.8 also prints discovery data. Those versions are not proposed upgrades.
The retained source has no direct `print` calls; `api.py` and `sock.py` have no
logging method calls. `camera.py` has two info calls and is outside these sock
contracts. The successful synthetic discovery test checks stdout, stderr and
library log records. This is limited evidence, not comprehensive log redaction,
dependency privacy certification or permission to log live payloads.

## Test boundary

[test_library_contracts.py](../tests/test_library_contracts.py) overrides the
method-level `mock_api` fixture only within that module. Real `OwletAPI` and
`Sock` methods run against a queued fake `session.request` boundary. Every
request must match its method, URL and keyword arguments, and every queued
request must be consumed. Unexpected requests and unapproved session closes
also fail fixture teardown, even if an exception were swallowed. Constructing
a real `aiohttp.ClientSession` fails and is tracked for teardown. The suite's
socket blocking remains enabled.

Regional endpoints, keys and sign-in application values are replaced with
synthetic values before execution. Identity-provider URLs contain only a
synthetic key. The fixed Android header names are checked without copying
vendor header values. Existing wholly synthetic JSON baselines are transformed
into HTTP property-list envelopes locally; no live captures or shared fixture
changes are needed. Time is controlled with the existing freezer fixture.

[test_dependency.py](../tests/test_dependency.py) additionally guards the exact
pin, Python/aiohttp metadata, public type imports and exception hierarchy.
The suites use the unchanged locked dependencies in [TESTING.md](TESTING.md).

## Observed contracts

| Area | Confirmed offline behaviour and coverage |
| --- | --- |
| Imports and exceptions | `OwletAPI`, `Sock`, `TokenDict`, `PropertiesDict` and all six concrete exception imports remain present. Authentication, connection, credential, device, email and password errors are direct siblings under `OwletError`; email/password/credential errors are not subclasses of `OwletAuthenticationError`. |
| Ordinary HTTP request | A validation GET of `/devices.json` precedes each requested operation. Only 200 and 201 are accepted. Tested 202/204/401/403/429/500/503 operation responses raise `OwletConnectionError` without parsing their bodies. They do not become authentication errors. |
| Validation | 200/201 return `None` without reading JSON. Every tested other status, including 202/204, 429 and 5xx, clears the access token and enters authentication/refresh. A 429 `Retry-After` response header is not used. This reproduces the existing classification concern; it does not test actual service limits. |
| Transport and cancellation | Connection errors and timeouts from validation or the operation propagate unchanged. Injected JSON decoding errors and `CancelledError` propagate unchanged from ordinary requests and all three refresh stages; entered response contexts exit with the same error type. This does not test Home Assistant setup/unload cancellation or a real aiohttp server. |
| Password exchange | Synthetic username/password are sent to verification; the returned refresh token enters the same three-stage refresh chain. `INVALID_PASSWORD`, `INVALID_EMAIL`, `EMAIL_NOT_FOUND`, `INVALID_LOGIN_CREDENTIALS`, throttled-attempt and unknown identity messages have explicit exception assertions. Passwords are absent from the returned token mapping. This does not claim the library erases its in-memory password attribute. |
| Refresh success | Refresh exchange, mini-token GET and token sign-in POST rotate refresh/access tokens and authorization. Expiry is current time plus `expires_in` minus 60 seconds. Missing, past and exactly-current expiry enter refresh; valid saved tokens perform validation. A request continues with the new authorization after validation refresh. |
| Refresh failure | Missing refresh fails without HTTP. Refresh status 400 raises `OwletAuthenticationError`; tested 401/403/429/503 raise exactly `OwletError`, preserving tokens for a direct refresh call. Mini/sign-in 401 raises authentication error after the new refresh token has already replaced the old one, while direct refresh retains old access/expiry. Partial state is observable; no atomicity or concurrent-refresh guarantee follows. |
| Rotation envelopes | A successful validation-triggered refresh changes `api.tokens`, but tested `get_properties` and `get_devices` results omit `tokens`: sign-in clears the changed flag and request validation discards the returned token mapping. This is a demonstrated library contract relevant to OWL-008, not a full storage/restart reproduction or a fix. |
| Discovery | Wire discovery is a list of `{"device": ...}` objects. The result wraps supported devices in `{"response": [...]}` and preserves their metadata. Each candidate's properties are fetched to detect V2/V3; unsupported candidates are still probed. `None` or an empty version filter selects both versions; explicit `[2]` and `[3]` filter correctly. Empty or wholly unsupported discovery raises `OwletDevicesError`. |
| Properties and activation | Each property read first posts `APP_ACTIVE=1`. The HTTP property list is indexed by property `name` and wrapped in `response`. `Sock.update_properties()` returns `raw_properties` and normalized `properties`; the `tokens` key is optional in observed results despite the typed dictionary declaring it required. |
| V2/V3 normalization | Synthetic V2 oxygen/heart/battery values become integers; V3 values become floats. Charging remains integer zero, boolean flags are converted, V3 revision is parsed, and V2 remains supported. V3 `last_updated` becomes `YYYY/MM/DD HH:MM:SS`, losing the source's UTC marker; this is not freshness validation. V3 sleep values 2, 8, 999 and string `"999"` become the corresponding integers without interpretation; V2's baseline has no sleep value. No new physiological meaning is assigned. |
| Commands | Both on and off commands first activate, then post `BASE_STATION_ON_CMD` with controlled integer timestamp and a JSON string containing `val` as `"true"`/`"false"`. `Sock.control_base_station` returns response truthiness: any nonempty mapping, including a synthetic error mapping, is `True`; empty mapping/list, `None` and `False` are `False`. It does not update local properties or prove an acknowledged device action. All writes are fake. |
| Session ownership | Explicit `OwletAPI.close()` closes even a supplied session. Normal tested methods leave the supplied session open. Home Assistant owns its shared session, so this observation must not be used to add library close calls to integration unload. |

Request counts below include validation and activation, with no refresh/retry:

| Public operation | HTTP calls |
| --- | --- |
| `request` | 2: validation + requested operation |
| `get_properties` / `Sock.update_properties` | 4: validation + activation + validation + property GET |
| `get_devices` with N candidates | 2 + 4N, including unsupported candidates |
| `Sock.control_base_station` | 4: validation + activation + validation + command |
| Direct successful refresh | 3: refresh + mini-token + sign-in |

A refresh inside validation adds three calls to the ordinary operation: the
tests observe 5 for `request`, 7 for properties and 9 for single-device discovery.
These are measured synthetic paths, not upper bounds. No timeout/backoff policy,
overlapping-refresh bound, current API rate limit or physical activation effect
is established. OWL-009/OWL-010 remain follow-up work in
[issue #12](https://github.com/Wiggi26/owlet/issues/12).

## Verification and remaining acceptance

Full Linux profile results and quality checks are recorded after execution in
the issue/PR handoff. The existing strict expected failures remain separate
from passing contract tests; none is removed by this preflight. Coverage still
measures integration source, not completeness of the external library tests.
Hassfest and HACS are hosted CI checks and must be checked on the eventual PR
head; they were not run locally.

The preflight supplies reviewed imports, hierarchy, discovery/measurement
envelopes, normalization, refresh, request counts and command results. It retains
the exact pin deliberately. Before proposing any successor, separately review
its current package availability, metadata, source hashes, exception/import and
privacy differences, then rerun these contracts on both locked profiles. A pin
change requires its own reviewed PR with compatibility and rollback evidence.

Still unverified: live Dream/European-account and firmware operation, real
network/TLS/content-type behaviour, comprehensive malformed-property policy,
freshness semantics, long-lived/concurrent refresh, partial-exchange recovery,
token persistence after process restart, and physical command/alarm behaviour.
Token concurrency/persistence remains [issue #8](https://github.com/Wiggi26/owlet/issues/8),
command handling remains [issue #15](https://github.com/Wiggi26/owlet/issues/15),
and target acceptance remains [issue #21](https://github.com/Wiggi26/owlet/issues/21).
No live login, Home Assistant/Proxmox access, deployment, release or official
alarm operation is part of this work. The integration remains supplemental to
the official Owlet app, base station and alarm system.
