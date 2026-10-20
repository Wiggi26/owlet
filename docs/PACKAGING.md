# HACS packaging

## Installation and versioning

Use HACS's [standard integration layout](https://www.hacs.xyz/docs/publish/integration/): `custom_components/owlet`, with `zip_release`, `filename`, and `content_in_root` omitted from `hacs.json`. HACS extracts this directory from the selected Git ref; no uploaded release ZIP or packaging workflow is required. The package includes `brand/icon.png`, copied unchanged from [Home Assistant Brands PR #4349](https://github.com/home-assistant/brands/pull/4349). The installed `NOTICE` records its pinned source, attribution and identification-only trademark status; the integration's Apache-2.0 licence does not grant rights to the mark.

The manifest reserves **2026.10.0**, currently unreleased. Continue calendar versions `YYYY.M.P`, starting `P` at 0 each month. A future GitHub Release tag must exactly match the manifest version and tested commit, without a leading `v`. Until releases exist, HACS tracks `main` by commit. Do not move published tags or reuse the mismatched upstream `2025.4.3` tag.

The unsupported HACS/Core minimum declarations were removed; a tested Core/Python support floor is still required. The runtime, domain, config/entity identities, translations, and exact dependency pin are unchanged. The installed directory includes the original licence text and a short attribution/modification notice; the root licence is unchanged.

## Dependency

`pyowletapi==2025.4.1` is available on PyPI, not yanked, and declares Python `>=3.10` and unpinned `aiohttp`. Its imported symbols and async method signatures match the integration. Versions 2025.4.8 and 2025.4.10 remain incompatible because they remove `OwletEmailError` and `OwletPasswordError`. Source hashes and the historical tag/ZIP mismatch are recorded in [AUDIT.md](AUDIT.md#dependency-versions-and-release-mismatch).

## Verification

The source-directory extraction check and HACS/hassfest passes at `c4de3fc` are historical evidence from 18 October 2026 ([PR #1](https://github.com/Wiggi26/owlet/pull/1)); they predate this local icon. For this asset, verify the PNG is 256×256 and its Git blob hash matches `06da0a79b6a8670cff9d13139c2176cc775fa0c5`, then inspect HACS extraction for `custom_components/owlet/brand/icon.png` and the existing installed files. Required current HACS and hassfest results are reported by the change's CI; this document adds no new test result.

Validation now runs on pushes and PRs only in `.github/workflows/validate.yml`, using reviewed action references, read-only permissions, and timeouts. There was no release-build workflow to remove. Repository topics `hacs`, `home-assistant`, and `owlet` were added to satisfy HACS discovery metadata; the initial topics failure is resolved.

Runtime options/authentication, freshness/validity, the test harness, and the tested support floor remain open in the audit. No release, deployment, live account/device test, or merge is part of this change.
