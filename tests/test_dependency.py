"""Keep the tested cloud-library version aligned with HACS installation."""

import json
from importlib.metadata import version
from pathlib import Path


def test_manifest_dependency_matches_environment():
    manifest = json.loads(Path("custom_components/owlet/manifest.json").read_text())
    assert manifest["requirements"] == [f"pyowletapi=={version('pyowletapi')}"]
