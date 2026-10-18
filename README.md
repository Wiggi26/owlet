# Owlet Custom Integration

<!-- Installation and update instructions revised for source-based HACS packaging. -->

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]

A custom component for the Owlet Smart Sock cloud service.

## Installation

1. In [HACS](https://www.hacs.xyz/docs/use/), open **⋮ → Custom repositories**, add `https://github.com/Wiggi26/owlet`, and select type **Integration**.
2. Open **Owlet** and download it. Until a release is published, select `main`.
3. Restart Home Assistant.
4. For a new installation, [add the integration][add-integration] or go to **Settings → Devices & services → Add integration → Owlet Smart Sock**. Enter your account credentials and select its cloud region (`europe` or `world`).

HACS installs directly from `custom_components/owlet` at the selected branch or release tag; no separately uploaded `owlet.zip` is required.

For manual installation, download the repository source archive and copy the contents of `custom_components/owlet` to `<config>/custom_components/owlet/`, including translations and licence files. Restart Home Assistant. The manifest must be at `<config>/custom_components/owlet/manifest.json`.

## Updates

Back up Home Assistant, download the update from HACS, and restart. Keep the existing Owlet configuration entry and entity IDs; deleting and re-adding the integration is unnecessary. Only one HACS repository should manage the `owlet` directory when switching from another repository.

Without published releases, HACS tracks updates to `main`. To roll back, redownload a previous release when available, or restore the integration files from a known-good commit/backup and restart. The upstream `2025.4.3` source tag and uploaded ZIP have different dependency pins; they are not interchangeable.

## Usage

The `Owlet` integration offers integration with the Owlet Smart Sock cloud service. This provides sensors such as heart rate, oxygen saturation, and charge percentage.

This integration provides the following entities:

- Binary sensors - charging status, high heart rate alert, low heart rate alert, high oxygen alert, low oxygen alert, low battery alert, lost power alert, sock disconnected alert, and sock status.
- Sensors - battery level, oxygen saturation, oxygen saturation 10 minute average, heart rate, battery time remaining, signal strength, and skin temperature.

## Options

- Seconds between polling - Number of seconds between each call for data from the Owlet cloud service, default is 5 seconds. Saved interval changes require a reload or restart.

## Troubleshooting

- If the integration is missing after download, check the manifest path above, restart, and inspect **Settings → System → Logs** for `custom_components.owlet`.
- If HACS requests `owlet.zip`, check that the selected repository/ref contains the source-installation HACS configuration.
- Import errors mentioning `OwletEmailError` or `OwletPasswordError` can result from incompatible dependency versions. This integration requires `pyowletapi==2025.4.1`; restart after installing matching integration files and let Home Assistant manage the dependency.
- Known Core options/reauthentication issues and measurement freshness limits are recorded in the [audit](docs/AUDIT.md). A Home Assistant/Python support range has not yet been verified.

[Report issues][issues] with integration, Home Assistant, and HACS versions, the installed ref, and a redacted error. Omit credentials, account/device identifiers, and readings.

Based on [Ryan Clark's original integration][upstream], licensed under [Apache-2.0][license].

[commits-shield]: https://img.shields.io/github/commit-activity/w/Wiggi26/owlet?style=for-the-badge
[commits]: https://github.com/Wiggi26/owlet/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license]: LICENSE
[license-shield]: https://img.shields.io/github/license/Wiggi26/owlet.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/Wiggi26/owlet.svg?style=for-the-badge
[releases]: https://github.com/Wiggi26/owlet/releases
[issues]: https://github.com/Wiggi26/owlet/issues
[upstream]: https://github.com/ryanbdclark/owlet
[add-integration]: https://my.home-assistant.io/redirect/config_flow_start?domain=owlet
