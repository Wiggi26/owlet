# Fixture provenance

`tests/fixture_data.py` generates all account, token, device and measurement records. Values are invented; email uses `example.invalid`, network addresses use the documentation range, and MAC addresses are synthetic/local. No fixture is a cloud capture or household export. Tests exercise the real pinned library's normalisation using these generated response envelopes.
