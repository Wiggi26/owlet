# HACS packaging decision and verification

Prepared 18 October 2026 for `Wiggi26/owlet`. This is a packaging change, with no application runtime or translation changes, release publication, or Home Assistant deployment.

## Decision

Use HACS's standard single-integration source layout:

```text
hacs.json
custom_components/
  owlet/
    manifest.json
    __init__.py
    ...platforms and helpers...
    translations/{en,fr,uk}.json
    LICENSE
    NOTICE
```

`hacs.json` only needs the fork's display name. `zip_release`, `filename`, and `content_in_root` are omitted; their defaults select the integration directory. The unused/unverified HACS `1.32.1` minimum and incorrect Core `2024.1` minimum are removed. No new minimum has been certified. This makes packaging installable without falsely promising runtime compatibility.

[HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/) specify this layout and make releases optional. [The HACS manifest/version documentation](https://www.hacs.xyz/docs/publish/start/) defines ZIP settings as optional and describes commit-based branch updates and release tags. The [official action](https://www.hacs.xyz/docs/publish/action/) validates push/PR branches using HACS's own validation code.

HACS still downloads a GitHub-generated source archive internally; the removed requirement is the separately built/uploaded **release asset** `owlet.zip`. The selected branch/tag is the source of truth for both the manifest dependency and installed files. HACS filters extraction to `custom_components/owlet`, excluding repository tests, fixtures, docs, and workflow files.

The only existing workflow was `.github/workflows/cron.yml`, containing hassfest and HACS jobs. There was no ZIP-build, upload, release, or deployment job to remove. The validation workflow is retained with reviewed action references, read-only contents permission, PR comments disabled, timeouts, concurrency, and manual invocation. It uses Ubuntu 24.04 and checkout v6's Node 24 runtime to avoid the runner transition/deprecated Node 20 warnings observed in the first run. Dependabot tracks the action references. The official action wrappers still invoke upstream-maintained container images; pinning wrapper commits does not freeze those images or certify a runtime support range.

The unchanged domain can use the existing [Owlet brand assets](https://github.com/home-assistant/brands/tree/master/custom_integrations/owlet). Official HACS validation accepts those assets, warning that it falls back to the central brands repository because there is no local icon. No new trademark artwork is introduced. `LICENSE` is unchanged at repository root and its text is copied into the installed directory, alongside `NOTICE`, so HACS source installs retain the licence and upstream attribution.

The fork is public, issues are enabled, and its existing description is present. Missing discovery topics were added as repository settings: `hacs`, `home-assistant`, and `owlet`. This setting change is outside the Git diff and is recorded here for review. The first push HACS run failed only the topics check; the subsequent PR run passed after that metadata correction. No checks were ignored.

## Dependency review

Retain **`pyowletapi==2025.4.1`**. PyPI metadata and source archives were retrieved again on 18 October 2026. All three versions below are available, not yanked, declare Python `>=3.10`, and declare `aiohttp` without a version bound.

| PyPI source | SHA-256 | Integration import compatibility |
| --- | --- | --- |
| [2025.4.1](https://pypi.org/project/pyowletapi/2025.4.1/) | `39c32fe5623d8c17eda43e12740ac5296fa60c27475070db69d775b53a1684a5` | Required exception classes are present. Retained exact pin. |
| [2025.4.8](https://pypi.org/project/pyowletapi/2025.4.8/) | `66a65d74b851edd7835c887bb0d47625a5396b59d4506df41b45aae63349faf0` | Removes `OwletEmailError` and `OwletPasswordError`; incompatible with unchanged integration imports. |
| [2025.4.10](https://pypi.org/project/pyowletapi/2025.4.10/) | `33a21c77adcc04663fcdbf1a0e845f37190512d72f662bc61c4cabeaf3c4b785` | Same removed exceptions; not an automatic upgrade candidate. |

All downloaded source hashes matched PyPI metadata. The pinned package is checked for every integration-imported library symbol and the constructor/authentication/discovery/poll/control method signatures. These checks establish dependency availability and the existing import/call contract, not successful cloud operation or compatibility across Home Assistant/Python/aiohttp versions. The inherited runtime test harness and tested Core support floor remain separate roadmap work.

## Version and release policy

Reserve manifest **`2026.10.0`**, marked **Unreleased** in the changelog, to distinguish the fork from upstream `2025.4.3`. Continue `YYYY.M.P` calendar versions, with `P` starting at 0 and increasing for each release within a month. No leading `v`. Integration version and cloud-library pin are independent.

When the owner separately approves a release:

1. Choose the exact reviewed commit, with passing HACS/hassfest and the then-required runtime checks. Confirm the selected Core/Python support floor and unresolved audit risks.
2. Set the manifest/changelog version in that commit; verify the tag is absent before creating it. The eventual GitHub Release tag must exactly equal `manifest.json`'s version.
3. Compare `git show <tag>:custom_components/owlet/manifest.json` with the tested commit's manifest, including `pyowletapi==2025.4.1` unless separately reviewed. Validate the tagged source archive and translations/licence/NOTICE. Do not reuse the mismatched upstream `2025.4.3` tag.
4. Publish a GitHub Release only by separate owner decision. No hand-built ZIP attachment is required. Do not move the tag or silently replace files under a published version.

Until a fork release exists, HACS uses `main` and identifies updates by commit. The manifest version alone neither publishes a release nor triggers a versioned HACS update. Old inherited tags remain untouched; select only reviewed fork versions or the updated default branch.

## Validation record

| Check | Observed result |
| --- | --- |
| [HACS PR validation](https://github.com/Wiggi26/owlet/actions/runs/39137887452/job/117706036027) | Passed, all 9 checks, at candidate `c2bd8f65527e445e40be62454e6fb555af410769`. Brands fallback warning described above; no ignored checks. |
| [Home Assistant hassfest PR validation](https://github.com/Wiggi26/owlet/actions/runs/39137887452/job/117706035723) | Passed at the same candidate. This is Home Assistant metadata validation, not a Core runtime test. |
| HACS source extraction | Passed for branch fallback and simulated release-tag scenarios; 15 files, three translations, licence/NOTICE, exact extracted byte equality, and no other repository files installed. |
| Dependency availability/import contract | Passed under Python 3.12.14 with installed `pyowletapi` 2025.4.1 and aiohttp 3.14.5. All 9 distinct imported library symbols and used async methods exist. No cloud call or HA setup was exercised. |
| Syntax and documentation | All repository JSON/YAML and Python ASTs parse; local Markdown targets and Git whitespace checks pass. |
| Runtime/identity source preservation | Diff against baseline `f8e0067` is empty for all integration Python, strings, translations, tests, and original root licence. The integration content tree is `31eaba4f6c21063749b67a3b4554b0373e440af0`. |
| Existing pytest suite | `pytest --collect-only -q --tb=short -p no:cacheprovider tests` with pytest 9.1.1 fails collection in five modules: the environment has no Home Assistant, and tests import a nonexistent Core integration rather than this custom component. No runtime tests are claimed to pass. |
| Existing Ruff baseline | Ruff 0.17.1 `check --isolated --no-cache custom_components tests` reports 9 existing lint errors; `format --isolated --no-cache --check custom_components tests` reports 11 files needing formatting, 5 already formatted. No source was reformatted. |

The PR retains final-head check results after documentation/workflow follow-ups; the links above identify the exact initially validated candidate. The installed integration tree is unchanged by those follow-ups.

Extraction procedure: export the staged Git source tree as a temporary repository ZIP with one top-level prefix. Retrieve and inspect HACS [`repositories/base.py` at `cc187cf258940a2a7acb5404773625465d7bf5a8`](https://github.com/hacs/integration/blob/cc187cf258940a2a7acb5404773625465d7bf5a8/custom_components/hacs/repositories/base.py). Its source SHA-256 is `bdb79af1fd36ca88a3eaca09ae7da1f21cb6ff8f762da4d5e230b1f7e96372d3`. Execute only the extracted `download_content` and `download_repository_zip` methods, with local transport/save/executor stubs, `zip_release=False`, `filename=None`, and remote path `custom_components/owlet`. For the `main` scenario the tag URL returns no archive and the branch URL supplies the candidate; for the simulated tag scenario the tag URL supplies the same candidate. Both produce exactly the expected integration files and identical bytes. Compare the installed licence text with the original after line-ending normalisation. No tag is created and no HACS/HA runtime is loaded by this isolated check.

## Remaining acceptance work

- No live HACS download, Home Assistant install, cloud authentication, or device operation was performed. User-run installation acceptance remains separate.
- A tested Core/Python support range is still missing. Known current-Core options/authentication defects and stale/invalid measurement handling remain open in [AUDIT.md](AUDIT.md).
- The existing Core-oriented tests are not a runnable custom-integration harness. Passing packaging checks cannot resolve that finding or certify entity-registry preservation through a live upgrade. Source identity is preserved because all runtime/translation files are unchanged.
- The historical upstream tag/ZIP mismatch remains historical evidence. The source-only fork policy removes that second packaging artifact for future versions; it does not repair or overwrite upstream releases.
