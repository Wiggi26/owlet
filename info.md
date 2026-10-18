# Owlet Custom Integration — Wiggi26 fork

Modified by Wiggi26 in October 2026 for public-fork installation and updates.
Derived from [Ryan Clark's Owlet integration](https://github.com/ryanbdclark/owlet), under [Apache-2.0](LICENSE).

Add `https://github.com/Wiggi26/owlet` in **HACS → ⋮ → Custom repositories**, with type **Integration**. Open **Owlet (Wiggi26 fork)**, download, and restart Home Assistant. Configure new installations in **Settings → Devices & services → Add integration → Owlet Smart Sock**.

For an existing installation, replace the integration files in place and keep the existing Home Assistant configuration entry. See the [README](https://github.com/Wiggi26/owlet#upgrading-an-existing-installation) for migration from upstream, backups, and rollback.

HACS installs `custom_components/owlet` from the selected Git ref; no uploaded ZIP asset is needed. Before the fork has a published release, use the default branch, `main`.

Runtime compatibility is not certified by packaging validation. The inherited Home Assistant 2024.1 minimum was incorrect; current Core options and authentication defects remain open in the [audit](https://github.com/Wiggi26/owlet/blob/main/docs/AUDIT.md). This integration is supplemental to the official Owlet app, base station, and alarms.

[Installation and troubleshooting](https://github.com/Wiggi26/owlet#installation) · [Report an issue](https://github.com/Wiggi26/owlet/issues)
