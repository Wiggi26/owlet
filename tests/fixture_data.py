"""Generate synthetic records; no captured cloud or household data is used."""

import json
from copy import deepcopy

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
DEFAULTS = {
    "oxygen_saturation": 98,
    "heart_rate": 100,
    "battery_percentage": 50,
    "battery_minutes": 400,
    "signal_strength": -30,
    "oxygen_10_av": 97,
    "base_station_on": True,
    "sock_connection": True,
    "skin_temperature": 34,
    "sleep_state": 8,
    "movement": 0,
    "movement_bucket": 0,
    "charging": 0,
    "hardware_version": "synthetic",
}
FLAGS = {
    "low_battery_alert": "LOW_BATT_ALRT",
    "low_heart_rate_alert": "LOW_HR_ALRT",
    "high_heart_rate_alert": "HIGH_HR_ALRT",
    "low_oxygen_alert": "LOW_OX_ALRT",
    "sock_disconnected": "SOCK_DISCON_ALRT",
    "sock_off": "SOCK_OFF",
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


def device(serial=SERIAL, index=1):
    """Return a generated device with a documentation-only network address."""
    return {
        "device": {
            "dsn": serial,
            "product_name": "Synthetic sock",
            "model": "Synthetic model",
            "sw_version": "test",
            "mac": f"02:00:00:00:00:{index:02x}",
            "lan_ip": f"192.0.2.{index}",
            "connection_status": "Online",
        }
    }


def properties(version=3, *, updated_at="2026-10-18T12:00:00Z", **changes):
    """Build an independent, explicit example of the pinned library's cloud schema."""
    values = {**DEFAULTS, **changes}
    flags = FLAGS | (
        {"high_oxygen_alert": "HIGH_OX_ALRT", "lost_power_alert": "LOST_POWER_ALRT"}
        if version == 3
        else {
            "critical_battery_alert": "CRIT_BATT_ALRT",
            "critical_oxygen_alert": "CRIT_OX_ALRT",
        }
    )
    raw = {
        cloud_key: {"value": values.get(key, False)} for key, cloud_key in flags.items()
    }
    if version == 3:
        vitals = {cloud_key: values[key] for key, cloud_key in V3_KEYS.items()}
        raw["REAL_TIME_VITALS"] = {
            "value": json.dumps(vitals),
            "data_updated_at": updated_at,
        }
        raw["oem_sock_version"] = {"value": json.dumps({"rev": 3})}
    else:
        raw.update(
            {cloud_key: {"value": values[key]} for key, cloud_key in V2_KEYS.items()}
        )
    return {"response": deepcopy(raw)}
