# Fixture provenance

The six JSON files retain the original fixture filenames with entirely synthetic contents. They describe discovery, discovery with token rotation, and V3 asleep/awake/charging and V2 property responses. Values were authored from the independent examples in `tests/fixture_data.py`, not copied or redacted from the inherited files. Identifiers, tokens, timestamps and readings are invented; network addresses use the documentation range and MAC addresses are synthetic/local. No fixture is a cloud capture or household export.

`tests/fixture_data.py` reads the files during test collection and returns a deep copy for each use. Helpers vary individual fields for multiple socks, malformed data and other edge cases. Tests pass these response envelopes through the real pinned library's normalisation. Keep the V3 `REAL_TIME_VITALS.value` field as a JSON-encoded string, matching the library's input contract.
