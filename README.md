# Owlet Custom Integration — Wiggi26 fork

[![GitHub Release](https://img.shields.io/github/v/release/Wiggi26/owlet)](https://github.com/Wiggi26/owlet/releases)
[![Validation](https://github.com/Wiggi26/owlet/actions/workflows/cron.yml/badge.svg)](https://github.com/Wiggi26/owlet/actions/workflows/cron.yml)
[![License](https://img.shields.io/github/license/Wiggi26/owlet)](LICENSE)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/)

A Home Assistant custom integration for the Owlet Smart Sock cloud service, maintained at [Wiggi26/owlet](https://github.com/Wiggi26/owlet). Derived from [Ryan Clark's original integration](https://github.com/ryanbdclark/owlet), which is archived. This README was modified by Wiggi26 in October 2026 for fork installation and updates.

The integration is supplemental to the official Owlet app, base station, and alarms. Cloud readings can be delayed or stale; do not use Home Assistant as a replacement alarm system.

## Compatibility and current limits

This packaging update keeps the existing runtime and `pyowletapi==2025.4.1`. It preserves the `owlet` domain, configuration entries, options, device identifiers, and entity unique IDs. It does not certify a Home Assistant support range or live Dream/European account compatibility.

The inherited Home Assistant `2024.1` minimum was incorrect: that Core version lacks an imported type. The unverified HACS/Core minimum declarations have been removed rather than replaced with an untested claim. Known options-flow and authentication-error defects on current Core remain open; see [the audit](docs/AUDIT.md) and [roadmap](docs/ROADMAP.md). Metadata validation does not establish runtime compatibility. A tested Core/Python support floor is still required before a stable release decision.

## Installation

### HACS custom repository

1. Install and configure [HACS](https://www.hacs.xyz/docs/use/), if needed.
2. In HACS, open **⋮ → Custom repositories**.
3. Add `https://github.com/Wiggi26/owlet`, select type **Integration**, and click **Add**.
4. Open **Owlet (Wiggi26 fork)**, confirm the repository owner is `Wiggi26`, and download it. Until this fork has a published release, choose the default branch, `main`. These instructions apply once the packaging PR has been merged into that branch.
5. Restart Home Assistant.
6. For a **new installation**, go to **Settings → Devices & services → Add integration → Owlet Smart Sock**, or use [Add integration](https://my.home-assistant.io/redirect/config_flow_start?domain=owlet). Enter your Owlet account credentials and select the account's existing cloud region (`europe` or `world`).

HACS downloads the integration directory from the selected branch or release tag. There is no separately uploaded `owlet.zip` asset to find or install. Adding the fork in HACS downloads code; it does not create a second Home Assistant configuration entry. See [HACS custom repository guidance](https://www.hacs.xyz/docs/faq/custom_repositories/).

### Manual installation

Download the source archive for a specific reviewed commit or release from [this fork](https://github.com/Wiggi26/owlet). Copy the **contents of `custom_components/owlet`**, including `translations`, `LICENSE`, and `NOTICE`, into `<config>/custom_components/owlet/`. The final manifest path must be `<config>/custom_components/owlet/manifest.json`, with no additional nested `owlet` folder. Restart Home Assistant, then follow step 6 above for a new installation. Manual installations require manual updates unless you later let HACS manage this same directory.

## Upgrading an existing installation

1. Make a Home Assistant backup and record the installed integration version and source repository/ref. Keep the backup private; it includes account tokens and may include recorded readings.
2. If already using this fork in HACS, open its repository and download the offered update, then restart Home Assistant. Check the release notes and [known issues](https://github.com/Wiggi26/owlet/issues) first.
3. To switch from upstream or another fork, add `Wiggi26/owlet` as a custom **Integration** repository and select it for the next download. Only one HACS repository should manage `custom_components/owlet`. If HACS reports that the domain is already managed, back up the folder, use the old repository's HACS **Remove** action to remove it from HACS, and download this fork before restarting. HACS removal can remove the code directory; it is separate from deleting the Owlet entry in **Settings → Devices & services**.
4. Retain the existing Home Assistant Owlet entry. Do not delete/re-add it, edit `.storage`, change region, or rename entities as an upgrade step. There is no configuration migration in this packaging change.
5. After restarting, verify the existing devices/entities and your dashboard/automation bindings. If authentication is requested, use the existing entry's reauthentication flow; record any known flow failure for the fork issue tracker.

Without published fork releases, HACS tracks `main` by commit, so changes merged there may be offered as updates. Once releases are published, HACS offers their tags. To reinstall or roll back, use HACS **Redownload** and select a previously reviewed fork release (when available), or manually restore the integration folder from the exact known-good commit/backup and restart. The upstream `2025.4.3` source tag is **not** interchangeable with its uploaded ZIP: their dependency pins differ. This change has no data migration; future migrations may require restoring a matching full backup to downgrade safely.

## Usage and options

Available entities depend on sock model, firmware, and properties returned by the cloud:

- Sensors include heart rate, oxygen saturation, 10-minute oxygen average, battery level/time remaining, signal strength, skin temperature, and sleep state. Movement sensors are disabled by default and can be enabled in the entity registry.
- Binary sensors include charging, sock/connection status, and available cloud alert flags.
- The existing base-station switch controls the base station. Keep it out of unattended alarm-silencing automations.

The default polling interval is five seconds; the options UI accepts five seconds or more. Saved changes currently require a reload/restart to reach running coordinators. The options UI itself has a known current-Core defect; do not remove the integration to work around it. This PR does not repair that defect.

Home Assistant's recorder, statistics, history, and backups can retain these readings. Review your own retention and sharing choices before exporting dashboards or diagnostics.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Fork does not appear in HACS | Add the exact public fork URL as type **Integration**, then refresh the HACS view. Confirm the repository owner. Merely searching for Owlet can select upstream. |
| HACS asks for `owlet.zip` | Check the selected repository/ref. Old upstream refs still request that asset. Use a fork ref containing the new `hacs.json`; retry/Redownload after refreshing repository information. |
| Integration is absent after download | Restart Home Assistant, check the manifest path above, and inspect **Settings → System → Logs** for `custom_components.owlet`. Avoid duplicate code folders. |
| Import error mentioning `OwletEmailError` or `OwletPasswordError` | This fork pins `pyowletapi==2025.4.1`. Confirm all files came from one ref, then restart and allow HA to install the requirement. Do not fix it by installing the newest library or using the mismatched upstream source tag. |
| Dependency installation fails | Check HA's outbound access to PyPI, DNS, and the dependency error in the log. Report the exact integration/Core/Python versions; do not install packages into HA OS by hand. |
| Authentication/no devices | Confirm credentials and account region in the official app. Account/firmware compatibility and existing reauth defects remain under investigation. Use the existing entry; avoid repeatedly deleting/recreating it or polling faster. |
| Options fail to open, or saved interval is unchanged | See the known Core options issue in the audit. Reload/restart applies an already saved interval; it does not fix the options-flow constructor. |
| Readings freeze, look implausible, or remain after disconnect | Consult the official Owlet app/base station. A successful cloud poll does not prove a fresh measurement. Freshness/validity fixes remain open. |

Report issues at [Wiggi26/owlet/issues](https://github.com/Wiggi26/owlet/issues) with the integration version, source/ref, HA Core/HACS versions, installation method, and a short redacted error. Remove email addresses, credentials/tokens, device/network identifiers, raw cloud payloads, and baby readings. Do not upload `.storage`, backups, or unredacted debug logs.

## Versioning and maintenance

The manifest reserves **`2026.10.0`** for the first fork release; it remains **unreleased**. Continue calendar versions `YYYY.M.P`, increasing `P` from 0 within a month. A future published GitHub Release must use a tag exactly matching `manifest.json` (for example `2026.10.0`, without `v`) on the tested commit. Do not move published tags or replace assets under an existing version. Integration and `pyowletapi` versions are independent.

Releases use the tagged repository sources; no release ZIP build/upload workflow is needed. Tags alone do not create a HACS release. Publication requires a separate owner decision after runtime and packaging gates pass. See [packaging decisions and verification](docs/PACKAGING.md) for validation evidence and unresolved limits.

## Attribution and licence

Original integration by **Ryan Clark and contributors**, retained under the [Apache License, Version 2.0](LICENSE). Upstream history and historical changelog links remain attributed to [ryanbdclark/owlet](https://github.com/ryanbdclark/owlet). Fork maintenance and issue reports belong at [Wiggi26/owlet](https://github.com/Wiggi26/owlet). See [NOTICE](NOTICE) for the fork modification notice; installed files include the licence and attribution.
