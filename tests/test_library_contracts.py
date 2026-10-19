"""OWL-017: observed contracts of the retained library, with no cloud access."""

import asyncio
import json
from collections import deque
from copy import deepcopy
from datetime import UTC, datetime
from unittest.mock import ANY

import aiohttp
import pytest
from pyowletapi import api as api_module
from pyowletapi.api import OwletAPI
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletCredentialsError,
    OwletDevicesError,
    OwletEmailError,
    OwletError,
    OwletPasswordError,
)
from pyowletapi.sock import Sock

from .fixture_data import INPUT, SERIAL, TOKENS, device, properties

BASE = "https://europe.example.invalid"
REFRESH = "https://securetoken.googleapis.com/v1/token?key=synthetic-key"
PASSWORD = (
    "https://www.googleapis.com/identitytoolkit/v3/relyingparty/"
    "verifyPassword?key=synthetic-key"
)
NOW = 1_800_000_000
ROTATED = {
    "api_token": "synthetic-rotated-access",
    "expiry": NOW + 3540,
    "refresh": "synthetic-rotated-refresh",
}
CLIENT_HEADERS = {"X-Android-Package": ANY, "X-Android-Cert": ANY}


class Reply:
    """A minimal aiohttp response; only explicitly queued requests can reach it."""

    def __init__(self, status=200, body=None, error=None, enter_error=None):
        self.status = status
        self.body = deepcopy(body)
        self.error = error
        self.enter_error = enter_error
        self.headers = {"Retry-After": "120"}
        self.json_calls = 0
        self.exit_types = []

    async def __aenter__(self):
        if self.enter_error is not None:
            raise self.enter_error
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        self.exit_types.append(exc_type)
        return False

    async def json(self):
        self.json_calls += 1
        if self.error is not None:
            raise self.error
        return deepcopy(self.body)


class QueuedSession:
    """Match method, URL and kwargs, fail on extra calls, and require exhaustion."""

    def __init__(self):
        self.pending = deque()
        self.calls = []
        self.unexpected = []
        self.close_calls = 0
        self.allow_close = False

    def expect(self, method, url, *, status=200, body=None, error=None, **kwargs):
        reply = Reply(status, body, error)
        self.pending.append((method, url, kwargs, reply))
        return reply

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, deepcopy(kwargs)))
        if not self.pending:
            self.unexpected.append("Unqueued HTTP request")
            raise AssertionError(self.unexpected[-1])
        expected_method, expected_url, expected_kwargs, reply = self.pending.popleft()
        if (method, url, kwargs) != (
            expected_method,
            expected_url,
            expected_kwargs,
        ):
            self.unexpected.append("HTTP request differs from queued contract")
            raise AssertionError(self.unexpected[-1])
        return reply

    async def close(self):
        self.close_calls += 1
        if not self.allow_close:
            self.unexpected.append("Unapproved session close")
            raise AssertionError(self.unexpected[-1])


@pytest.fixture(autouse=True)
def mock_api():
    """Override conftest's method mocks only here to exercise the real library."""


@pytest.fixture
def client(monkeypatch, freezer):
    """Keep sockets blocked and forbid creation of any real HTTP session."""
    freezer.move_to(datetime.fromtimestamp(NOW, UTC))
    unexpected_sessions = []

    def forbidden_session(*args, **kwargs):
        unexpected_sessions.append("Unapproved ClientSession construction")
        raise AssertionError(unexpected_sessions[-1])

    monkeypatch.setattr(aiohttp, "ClientSession", forbidden_session)
    # Replace endpoints and embedded vendor credentials; never copy them into tests.
    monkeypatch.setattr(
        api_module,
        "REGION_INFO",
        {
            region: {
                "url_base": f"https://{region}.example.invalid",
                "apiKey": "synthetic-key",
                "url_mini": f"https://{region}.example.invalid/mini",
                "url_signin": f"https://{region}.example.invalid/signin",
                "app_id": "synthetic-app",
                "app_secret": "synthetic-secret",
            }
            for region in ("europe", "world")
        },
    )
    session = QueuedSession()
    api = OwletAPI(
        region="europe",
        token=TOKENS["api_token"],
        expiry=TOKENS["expiry"],
        refresh=TOKENS["refresh"],
        session=session,
    )
    yield api, session
    assert not unexpected_sessions
    assert not session.unexpected
    assert not session.pending, "Not all expected HTTP calls were made"
    assert session.close_calls == int(session.allow_close)


def validation(session, *, status=200, token=TOKENS["api_token"]):
    """Every ordinary request first probes the devices endpoint."""
    return session.expect(
        "GET",
        BASE + "/devices.json",
        status=status,
        headers={"Authorization": "auth_token " + token},
    )


def request(session, method, path, *, token=TOKENS["api_token"], data=None, **reply):
    validation(session, token=token)
    return session.expect(
        method,
        BASE + path,
        headers={"Authorization": "auth_token " + token},
        json=data,
        **reply,
    )


def refresh_exchange(session, *, old_refresh=TOKENS["refresh"]):
    """Queue the actual refresh -> mini-token -> sign-in HTTP exchange."""
    session.expect(
        "POST",
        REFRESH,
        data={"grantType": "refresh_token", "refreshToken": old_refresh},
        headers=CLIENT_HEADERS,
        body={"refresh_token": ROTATED["refresh"], "id_token": "synthetic-id"},
    )
    session.expect(
        "GET",
        BASE + "/mini",
        headers={"Authorization": "synthetic-id"},
        body={"mini_token": "synthetic-mini"},
    )
    session.expect(
        "POST",
        BASE + "/signin",
        json={
            "app_id": "synthetic-app",
            "app_secret": "synthetic-secret",
            "provider": "owl_id",
            "token": "synthetic-mini",
        },
        body={"access_token": ROTATED["api_token"], "expires_in": 3600},
    )


def property_read(
    session, version=3, *, serial=SERIAL, token=TOKENS["api_token"], **changes
):
    """Convert the synthetic baseline to the library's wire property list."""
    raw = (
        properties(version, **changes)["response"]
        if version
        else {"UNSUPPORTED": {"value": 0}}
    )
    request(
        session,
        "GET",
        f"/dsns/{serial}/properties.json",
        token=token,
        body=[{"property": {"name": name, **value}} for name, value in raw.items()],
    )
    return {name: {"name": name, **value} for name, value in raw.items()}


def property_requests(
    session, version=3, *, serial=SERIAL, token=TOKENS["api_token"], **changes
):
    request(
        session,
        "POST",
        f"/dsns/{serial}/properties/APP_ACTIVE/datapoints.json",
        token=token,
        data={"datapoint": {"metadata": {}, "value": 1}},
        body={"synthetic": True},
    )
    return property_read(session, version, serial=serial, token=token, **changes)


@pytest.mark.parametrize("status", [200, 201, 202, 204, 401, 403, 429, 500, 503])
async def test_request_status_contract(client, status):
    api, session = client
    reply = request(session, "GET", "/synthetic.json", status=status, body={"ok": 1})
    if status in (200, 201):
        assert await api.request("GET", "/synthetic.json") == {"ok": 1}
        assert reply.json_calls == 1
    else:
        with pytest.raises(OwletConnectionError, match="^Error sending request$"):
            await api.request("GET", "/synthetic.json")
        assert reply.json_calls == 0
    assert len(session.calls) == 2
    assert api.tokens == TOKENS


@pytest.mark.parametrize("status", [200, 201])
async def test_validation_success_does_not_read_body(client, status):
    api, session = client
    reply = validation(session, status=status)
    assert await api.authenticate() is None
    assert reply.json_calls == 0
    assert len(session.calls) == 1


@pytest.mark.parametrize("status", [202, 204, 401, 403, 429, 500, 503])
async def test_validation_non_success_refreshes_even_for_transient_status(
    client, status
):
    api, session = client
    reply = validation(session, status=status)
    refresh_exchange(session)
    assert await api.validate_authentication() == ROTATED
    assert api.tokens == ROTATED
    assert api.headers == {"Authorization": "auth_token " + ROTATED["api_token"]}
    assert reply.json_calls == 0
    assert len(session.calls) == 4


async def test_request_resumes_with_rotated_authorization(client):
    api, session = client
    validation(session, status=401)
    refresh_exchange(session)
    session.expect(
        "GET",
        BASE + "/synthetic.json",
        headers={"Authorization": "auth_token " + ROTATED["api_token"]},
        json=None,
        body={"ok": True},
    )
    assert await api.request("GET", "/synthetic.json") == {"ok": True}
    assert len(session.calls) == 5
    assert api.tokens == ROTATED


@pytest.mark.parametrize("expiry", [None, NOW - 1, NOW])
async def test_expired_authentication_uses_three_request_refresh(client, expiry):
    api, session = client
    api._expiry = expiry
    refresh_exchange(session)
    assert await api.authenticate() == ROTATED
    assert api.tokens == ROTATED
    assert len(session.calls) == 3


async def test_password_authentication_exchanges_only_synthetic_credentials(client):
    api, session = client
    api._auth_token = api._refresh = None
    api._user, api._password = INPUT["username"], INPUT["password"]
    session.expect(
        "POST",
        PASSWORD,
        data={
            "email": INPUT["username"],
            "password": INPUT["password"],
            "returnSecureToken": True,
        },
        headers=CLIENT_HEADERS,
        body={"refreshToken": "synthetic-password-refresh"},
    )
    refresh_exchange(session, old_refresh="synthetic-password-refresh")
    assert await api.authenticate() == ROTATED
    assert set(api.tokens) == {"api_token", "expiry", "refresh"}
    assert len(session.calls) == 4


@pytest.mark.parametrize(
    ("message", "exception"),
    [
        ("INVALID_PASSWORD", OwletPasswordError),
        ("INVALID_EMAIL", OwletEmailError),
        ("EMAIL_NOT_FOUND", OwletEmailError),
        ("INVALID_LOGIN_CREDENTIALS", OwletCredentialsError),
        ("TOO_MANY_ATTEMPTS_TRY_LATER", OwletAuthenticationError),
        ("SYNTHETIC_UNRECOGNIZED", OwletAuthenticationError),
    ],
)
async def test_password_error_classes(client, message, exception):
    api, session = client
    session.expect(
        "POST",
        PASSWORD,
        status=400,
        data={"email": None, "password": None, "returnSecureToken": True},
        headers=CLIENT_HEADERS,
        body={"error": {"message": message}},
    )
    with pytest.raises(exception):
        await api.password_verification()
    assert api.tokens == TOKENS


@pytest.mark.parametrize(
    ("status", "exception"),
    [
        (400, OwletAuthenticationError),
        (401, OwletError),
        (403, OwletError),
        (429, OwletError),
        (503, OwletError),
    ],
)
async def test_failed_refresh_preserves_existing_tokens(client, status, exception):
    api, session = client
    session.expect(
        "POST",
        REFRESH,
        status=status,
        data={"grantType": "refresh_token", "refreshToken": TOKENS["refresh"]},
        headers=CLIENT_HEADERS,
        body={"error": "synthetic"},
    )
    with pytest.raises(exception) as caught:
        await api.refresh_authentication()
    assert type(caught.value) is exception
    assert api.tokens == TOKENS


@pytest.mark.parametrize("stage", ["mini", "signin"])
async def test_partial_refresh_keeps_new_refresh_with_old_access_token(client, stage):
    api, session = client
    refresh_exchange(session)
    if stage == "mini":
        session.pending.pop()  # The sign-in must not be attempted after mini failure.
    failed_reply = session.pending[-1][-1]
    failed_reply.status = 401
    with pytest.raises(OwletAuthenticationError):
        await api.refresh_authentication()
    assert api.tokens == {**TOKENS, "refresh": ROTATED["refresh"]}
    assert api.headers == {"Authorization": "auth_token " + TOKENS["api_token"]}
    assert len(session.calls) == (2 if stage == "mini" else 3)


async def test_no_refresh_token_fails_without_http(client):
    api, session = client
    api._refresh = None
    with pytest.raises(OwletAuthenticationError, match="^No refresh token supplied$"):
        await api.refresh_authentication()
    assert not session.calls


@pytest.mark.parametrize("stage", ["request", "refresh", "mini", "signin"])
@pytest.mark.parametrize("failure", ["malformed-json", "cancelled"])
async def test_json_error_and_cancellation_propagate(client, stage, failure):
    api, session = client
    error = (
        json.JSONDecodeError("Synthetic malformed JSON", "invalid", 0)
        if failure == "malformed-json"
        else asyncio.CancelledError()
    )
    if stage == "request":
        reply = request(session, "GET", "/synthetic.json", error=error)
        operation = api.request("GET", "/synthetic.json")
    else:
        refresh_exchange(session)
        keep = {"refresh": 1, "mini": 2, "signin": 3}[stage]
        while len(session.pending) > keep:
            session.pending.pop()
        reply = session.pending[-1][-1]
        reply.error = error
        operation = api.refresh_authentication()
    with pytest.raises(type(error)) as caught:
        await operation
    assert caught.value is error
    assert reply.exit_types == [type(error)]
    expected_tokens = (
        {**TOKENS, "refresh": ROTATED["refresh"]}
        if stage in ("mini", "signin")
        else TOKENS
    )
    assert api.tokens == expected_tokens


@pytest.mark.parametrize("stage", ["validation", "request"])
@pytest.mark.parametrize("error_type", [aiohttp.ClientConnectionError, TimeoutError])
async def test_transport_failures_propagate_without_refresh(client, stage, error_type):
    api, session = client
    error = error_type("Synthetic transport failure")
    if stage == "validation":
        reply = validation(session)
    else:
        reply = request(session, "GET", "/synthetic.json")
    reply.enter_error = error
    with pytest.raises(error_type) as caught:
        await api.request("GET", "/synthetic.json")
    assert caught.value is error
    assert api.tokens == TOKENS
    assert len(session.calls) == (1 if stage == "validation" else 2)


@pytest.mark.parametrize("versions", [None, [], [2], [3]])
async def test_discovery_filters_v2_v3_and_preserves_device_envelope(
    client, versions, capsys, caplog
):
    api, session = client
    devices = [
        device(f"SYNTHETIC-SOCK-{version}", version + 1) for version in (2, 3, 0)
    ]
    request(session, "GET", "/devices.json", body=devices)
    for version in (2, 3, 0):
        property_requests(session, version, serial=f"SYNTHETIC-SOCK-{version}")
    result = await api.get_devices(versions)
    supported = versions or [2, 3]
    assert result == {
        "response": [
            d for v, d in zip((2, 3, 0), devices, strict=True) if v in supported
        ]
    }
    assert len(session.calls) == 14
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert not [
        record for record in caplog.records if record.name.startswith("pyowletapi")
    ]


@pytest.mark.parametrize("unsupported", [False, True])
async def test_discovery_without_supported_devices_raises(client, unsupported):
    api, session = client
    request(session, "GET", "/devices.json", body=[device()] if unsupported else [])
    if unsupported:
        property_requests(session, 0)
    with pytest.raises(OwletDevicesError, match="^No devices found$"):
        await api.get_devices()
    assert len(session.calls) == (6 if unsupported else 2)


@pytest.mark.parametrize("version", [2, 3])
async def test_actual_http_properties_and_sock_normalization(client, version):
    api, session = client
    raw = property_requests(session, version)
    sock = Sock(api, device()["device"])
    result = await sock.update_properties()
    assert result == {"raw_properties": raw, "properties": sock.properties}
    assert sock.version == version
    assert sock.serial == SERIAL
    assert sock.revision == (3 if version == 3 else None)
    assert sock.properties["oxygen_saturation"] == 98
    assert sock.properties["heart_rate"] == 100
    assert sock.properties["battery_percentage"] == 50
    assert sock.properties["base_station_on"] is True
    assert sock.properties["charging"] == 0
    assert type(sock.properties["charging"]) is int
    assert type(sock.properties["oxygen_saturation"]) is (
        float if version == 3 else int
    )
    assert sock.properties["low_heart_rate_alert"] is False
    if version == 3:
        assert sock.properties["last_updated"] == "2026/10/18 12:00:00"
        assert sock.properties["sleep_state"] == 8
    else:
        assert "last_updated" not in sock.properties
    assert len(session.calls) == 4


@pytest.mark.parametrize("operation", ["properties", "devices"])
async def test_validation_rotation_updates_client_but_omits_envelope_tokens(
    client, operation
):
    api, session = client
    validation(session, status=401)
    refresh_exchange(session)
    path = (
        f"/dsns/{SERIAL}/properties/APP_ACTIVE/datapoints.json"
        if operation == "properties"
        else "/devices.json"
    )
    session.expect(
        "POST" if operation == "properties" else "GET",
        BASE + path,
        headers={"Authorization": "auth_token " + ROTATED["api_token"]},
        json={"datapoint": {"metadata": {}, "value": 1}}
        if operation == "properties"
        else None,
        body=None if operation == "properties" else [device()],
    )
    if operation == "properties":
        raw = property_read(session, token=ROTATED["api_token"])
        result = await api.get_properties(SERIAL)
        assert result == {"response": raw}
    else:
        property_requests(session, token=ROTATED["api_token"])
        result = await api.get_devices()
        assert result == {"response": [device()]}
    assert api.tokens == ROTATED
    assert "tokens" not in result
    assert len(session.calls) == (7 if operation == "properties" else 9)


@pytest.mark.parametrize("code", [2, 8, 999, "999"])
async def test_v3_sleep_normalization_preserves_integer_code(client, code):
    api, session = client
    property_requests(session, sleep_state=code)
    sock = Sock(api, device()["device"])
    result = await sock.update_properties()
    assert result["properties"]["sleep_state"] == int(code)
    assert type(result["properties"]["sleep_state"]) is int


@pytest.mark.parametrize("on", [False, True])
@pytest.mark.parametrize(
    "body", [{"synthetic": True}, {"error": "synthetic-rejected"}, {}, [], None, False]
)
async def test_base_station_command_boolean_is_response_truthiness(client, on, body):
    api, session = client
    sock = Sock(api, device()["device"])
    request(
        session,
        "POST",
        f"/dsns/{SERIAL}/properties/APP_ACTIVE/datapoints.json",
        data={"datapoint": {"metadata": {}, "value": 1}},
    )
    request(
        session,
        "POST",
        f"/dsns/{SERIAL}/properties/BASE_STATION_ON_CMD/datapoints.json",
        data={
            "datapoint": {
                "metadata": {},
                "value": json.dumps({"ts": NOW, "val": "true" if on else "false"}),
            }
        },
        body=body,
    )
    assert await sock.control_base_station(on) is bool(body)
    assert len(session.calls) == 4
    assert sock.properties == {}


async def test_close_closes_supplied_session(client):
    api, session = client
    session.allow_close = True
    await api.close()
    assert session.close_calls == 1
