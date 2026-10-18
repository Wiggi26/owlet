"""Load synthetic JSON baselines and make isolated variations for regression tests."""

import json
from copy import deepcopy
from pathlib import Path

SERIAL = "SYNTHETIC-SOCK-001"
TOKENS = {
    "api_token": "synthetic-access",
    "expiry": 2000000000,
    "refresh": "synthetic-refresh",
}
INPUT = {
    "region": "europe",
    "username": "parent@example.invalid",
    "password": "synthetic-password",
}
FLAGS = {
    "low_battery_alert": "LOW_BATT_ALRT",
    "low_heart_rate_alert": "LOW_HR_ALRT",
    "high_heart_rate_alert": "HIGH_HR_ALRT",
    "low_oxygen_alert": "LOW_OX_ALRT",
    "sock_disconnected": "SOCK_DISCON_ALRT",
    "sock_off": "SOCK_OFF",
    "high_oxygen_alert": "HIGH_OX_ALRT",
    "lost_power_alert": "LOST_POWER_ALRT",
    "critical_battery_alert": "CRIT_BATT_ALRT",
    "critical_oxygen_alert": "CRIT_OX_ALRT",
}
V3_KEYS = {
    "oxygen_saturation": "ox",
    "heart_rate": "hr",
    "battery_percentage": "bat",
    "battery_minutes": "btt",
    "signal_strength": "rsi",
    "oxygen_10_av": "oxta",
    "base_station_on": "bso",
    "skin_temperature": "st",
    "sleep_state": "ss",
    "movement": "mv",
    "movement_bucket": "mvb",
    "charging": "chg",
}
V2_KEYS = {
    "oxygen_saturation": "OXYGEN_LEVEL",
    "heart_rate": "HEART_RATE",
    "battery_percentage": "BATT_LEVEL",
    "signal_strength": "BLE_RSSI",
    "base_station_on": "BASE_STATION_ON",
    "sock_connection": "SOCK_CONNECTION",
    "movement": "MOVEMENT",
    "charging": "CHARGE_STATUS",
    "hardware_version": "oem_sock_version",
}

# Read files during test collection, outside Home Assistant's event loop.
_FIXTURES = {
    path.name: json.loads(path.read_text(encoding="utf-8"))
    for path in Path(__file__).with_name("fixtures").glob("*.json")
}


def load_fixture(name):
    """Return a fresh copy so mutations never affect another test's baseline."""
    return deepcopy(_FIXTURES[name])


def device(serial=SERIAL, index=1):
    """Vary the JSON discovery example for multiple synthetic socks."""
    payload = load_fixture("get_devices.json")["response"][0]
    payload["device"].update(
        dsn=serial, mac=f"02:00:00:00:00:{index:02x}", lan_ip=f"192.0.2.{index}"
    )
    return payload


def properties(version=3, *, scenario="asleep", updated_at=None, **changes):
    """Copy a baseline response, then vary only the fields a regression needs."""
    suffix = "v2" if version == 2 else scenario
    payload = load_fixture(f"update_properties_{suffix}.json")
    raw = payload["response"]
    if version == 3:
        vitals = json.loads(raw["REAL_TIME_VITALS"]["value"])
        for key, value in changes.items():
            if key in V3_KEYS:
                vitals[V3_KEYS[key]] = value
            else:
                raw[FLAGS[key]]["value"] = value
        raw["REAL_TIME_VITALS"]["value"] = json.dumps(vitals)
        if updated_at is not None:
            raw["REAL_TIME_VITALS"]["data_updated_at"] = updated_at
    else:
        keys = V2_KEYS | FLAGS
        for key, value in changes.items():
            raw[keys[key]]["value"] = value
    return payload
