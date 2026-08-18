import json
import tempfile
from pathlib import Path

from libraries.utils.visualization.visualisation_helpers import (
    build_v2_scenario_metadata_json,
)


def test_build_v2_scenario_metadata_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        metadata_path = build_v2_scenario_metadata_json(
            base_dir=str(base_dir),
            label_explanations={
                "Structured": "Struktureret rute med sektionsregler."
            },
            apr_explanations={
                "O18": "Profil for omdelere over 18 år."
            },
            revenue_explanations={
                "U36": "Omsætning baseret på uge 36."
            },
        )
        metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        assert metadata["labels"]["Structured"] == (
            "Struktureret rute med sektionsregler."
        )
        assert metadata["APR_profiles"]["O18"] == (
            "Profil for omdelere over 18 år."
        )
        assert metadata["week_profiles"]["U36"] == (
            "Omsætning baseret på uge 36."
        )
