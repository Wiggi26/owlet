# HACS packaging

## Installation and versioning

Use HACS's [standard integration layout](https://www.hacs.xyz/docs/publish/integration/): `custom_components/owlet`, with `zip_release`, `filename`, and `content_in_root` omitted from `hacs.json`. HACS extracts this directory from the selected Git ref; no uploaded release ZIP or packaging workflow is required. Existing central Owlet brand assets satisfy HACS validation, with a warning about the absent local icon.

The manifest reserves **2026.10.0**, currently unreleased. Continue calendar versions `YYYY.M.P`, starting `P` at 0 each month. A future GitHub Release tag must exactly match the manifest version and tested commit, without a leading `v`. Until releases exist, HACS tracks `main` by commit. Do not move published tags or reuse the mismatched upstream `2025.4.3` tag.

The unsupported HACS/Core minimum declarations were removed; a tested Core/Python support floor is still required. The runtime, domain, config/entity identities, translations, and exact dependency pin are unchanged. The installed directory includes the original licence text and a short attribution/modification notice; the root licence is unchanged.

## Dependency

`pyowletapi==2025.4.1` is available on PyPI, not yanked, and declares Python `>=3.10` and unpinned `aiohttp`. Its imported symbols and async method signatures match the integration. Versions 2025.4.8 and 2025.4.10 remain incompatible because they remove `OwletEmailError` and `OwletPasswordError`. Source hashes and the historical tag/ZIP mismatch are recorded in [AUDIT.md](AUDIT.md#dependency-versions-and-release-mismatch).

## Verification

- [HACS](https://github.com/Wiggi26/owlet/actions/runs/39138090317/job/117706642129) and [hassfest](https://github.com/Wiggi26/owlet/actions/runs/39138090317/job/117706641903) passed at `c4de3fc`; final-head results are linked in the PR. No checks are ignored.
- HACS's `download_content` and `download_repository_zip` methods at [revision cc187cf](https://github.com/hacs/integration/blob/cc187cf258940a2a7acb5404773625465d7bf5a8/custom_components/hacs/repositories/base.py) were exercised against a local Git source archive with stubbed transport. Branch fallback and simulated tag extraction produced all 15 expected files byte-for-byte, including three translations, LICENSE and NOTICE, with no repository tests/docs/fixtures installed. No tag was created or live HACS/HA instance used.
- Dependency imports passed under Python 3.12.14 with aiohttp 3.14.5; downloaded source hashes matched PyPI. This does not establish a Home Assistant runtime support range.
- JSON/YAML/Python parsing, local documentation paths, whitespace checks, and runtime-source preservation checks passed. Existing pytest collection fails in five modules; Ruff reports nine existing lint findings and 11 files needing formatting.

Validation now runs on pushes and PRs only in `.github/workflows/validate.yml`, using reviewed action references, read-only permissions, and timeouts. There was no release-build workflow to remove. Repository topics `hacs`, `home-assistant`, and `owlet` were added to satisfy HACS discovery metadata; the initial topics failure is resolved.

Runtime options/authentication, freshness/validity, the test harness, and the tested support floor remain open in the audit. No release, deployment, live account/device test, or merge is part of this change.
